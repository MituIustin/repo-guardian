from urllib.parse import quote, urlencode

import httpx

from app.github.schemas import (
    GitHubBranch,
    GitHubEmail,
    GitHubJob,
    GitHubRepository,
    GitHubToken,
    GitHubUserProfile,
)

GITHUB_API_VERSION = "2022-11-28"


class GitHubOAuthError(Exception):
    """Raised when GitHub rejects or cannot complete an OAuth operation."""


class GitHubOAuthClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        callback_url: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url
        self.http_client = http_client

    def authorization_url(self, state: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.callback_url,
                "scope": "read:user user:email repo",
                "state": state,
            }
        )
        return f"https://github.com/login/oauth/authorize?{query}"

    async def exchange_code(self, code: str) -> GitHubToken:
        response = await self._request(
            "POST",
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.callback_url,
            },
            headers={"Accept": "application/json"},
        )
        try:
            payload = response.json()
            if "error" in payload or "access_token" not in payload:
                raise GitHubOAuthError("GitHub did not return an access token")
            return GitHubToken.model_validate(payload)
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid token response") from error

    async def get_user(self, access_token: str) -> GitHubUserProfile:
        headers = self._api_headers(access_token)
        response = await self._request("GET", "https://api.github.com/user", headers=headers)
        try:
            profile = GitHubUserProfile.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid user profile") from error

        if profile.email is None:
            profile.email = await self._get_primary_email(access_token)

        return profile

    async def list_repositories(self, access_token: str) -> list[GitHubRepository]:
        repositories: list[GitHubRepository] = []
        for page in range(1, 11):
            response = await self._request(
                "GET",
                "https://api.github.com/user/repos",
                headers=self._api_headers(access_token),
                params={
                    "affiliation": "owner,collaborator,organization_member",
                    "sort": "updated",
                    "per_page": 100,
                    "page": page,
                },
            )
            payload = self._list_payload(response, "repository")
            repositories.extend(GitHubRepository.model_validate(item) for item in payload)
            if len(payload) < 100:
                break
        return repositories

    async def get_repository(
        self, access_token: str, github_repository_id: int
    ) -> GitHubRepository:
        response = await self._request(
            "GET",
            f"https://api.github.com/repositories/{github_repository_id}",
            headers=self._api_headers(access_token),
        )
        try:
            return GitHubRepository.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid repository") from error

    async def list_branches(
        self, access_token: str, repository_full_name: str
    ) -> list[GitHubBranch]:
        owner, name = repository_full_name.split("/", maxsplit=1)
        response = await self._request(
            "GET",
            f"https://api.github.com/repos/{quote(owner)}/{quote(name)}/branches",
            headers=self._api_headers(access_token),
            params={"per_page": 100},
        )
        payload = self._list_payload(response, "branch")
        return [GitHubBranch.model_validate(item) for item in payload]

    async def list_workflow_jobs(
        self, access_token: str, repository_full_name: str, github_run_id: int
    ) -> list[GitHubJob]:
        owner, name = repository_full_name.split("/", maxsplit=1)
        response = await self._request(
            "GET",
            f"https://api.github.com/repos/{quote(owner)}/{quote(name)}/actions/runs/{github_run_id}/jobs",
            headers=self._api_headers(access_token),
            params={"per_page": 100, "filter": "latest"},
        )
        try:
            payload = response.json()
            jobs = payload.get("jobs") if isinstance(payload, dict) else None
            if not isinstance(jobs, list):
                raise TypeError("Expected a jobs list")
            return [GitHubJob.model_validate(item) for item in jobs]
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid job list") from error

    async def download_workflow_logs(
        self, access_token: str, repository_full_name: str, github_run_id: int
    ) -> bytes:
        owner, name = repository_full_name.split("/", maxsplit=1)
        response = await self._request(
            "GET",
            f"https://api.github.com/repos/{quote(owner)}/{quote(name)}/actions/runs/{github_run_id}/logs",
            headers=self._api_headers(access_token),
            follow_redirects=True,
        )
        return response.content

    async def rerun_workflow(
        self,
        access_token: str,
        repository_full_name: str,
        github_run_id: int,
        *,
        failed_jobs_only: bool = False,
    ) -> None:
        owner, name = repository_full_name.split("/", maxsplit=1)
        action = "rerun-failed-jobs" if failed_jobs_only else "rerun"
        await self._request(
            "POST",
            f"https://api.github.com/repos/{quote(owner)}/{quote(name)}/actions/runs/"
            f"{github_run_id}/{action}",
            headers=self._api_headers(access_token),
        )

    async def rerun_job(
        self,
        access_token: str,
        repository_full_name: str,
        github_job_id: int,
    ) -> None:
        owner, name = repository_full_name.split("/", maxsplit=1)
        await self._request(
            "POST",
            f"https://api.github.com/repos/{quote(owner)}/{quote(name)}/actions/jobs/"
            f"{github_job_id}/rerun",
            headers=self._api_headers(access_token),
        )

    async def _get_primary_email(self, access_token: str) -> str | None:
        response = await self._request(
            "GET",
            "https://api.github.com/user/emails",
            headers=self._api_headers(access_token),
        )
        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("GitHub email response must be a list")
            emails = [GitHubEmail.model_validate(item) for item in payload]
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid email response") from error
        primary = next((item for item in emails if item.primary and item.verified), None)
        return primary.email if primary else None

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            if self.http_client is not None:
                response = await self.http_client.request(method, url, **kwargs)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, ValueError) as error:
            raise GitHubOAuthError("GitHub OAuth request failed") from error

    @staticmethod
    def _api_headers(access_token: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    @staticmethod
    def _list_payload(response: httpx.Response, resource_name: str) -> list[object]:
        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Expected a list response")
            return payload
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError(
                f"GitHub returned an invalid {resource_name} list"
            ) from error
