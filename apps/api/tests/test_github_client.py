from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.github.client import GitHubOAuthClient


def test_authorization_url_contains_callback_scope_and_state() -> None:
    client = GitHubOAuthClient(
        client_id="client-id",
        client_secret="client-secret",
        callback_url="http://localhost:8000/api/auth/github/callback",
    )
    authorization_url = client.authorization_url("csrf-state")
    query = parse_qs(urlparse(authorization_url).query)

    assert authorization_url.startswith("https://github.com/login/oauth/authorize?")
    assert query["client_id"] == ["client-id"]
    assert query["state"] == ["csrf-state"]
    assert query["scope"] == ["read:user user:email repo"]


@pytest.mark.asyncio
async def test_exchange_code_and_load_profile_with_primary_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login/oauth/access_token":
            return httpx.Response(
                200,
                json={"access_token": "token", "token_type": "bearer", "scope": "read:user"},
            )
        if request.url.path == "/user":
            return httpx.Response(
                200,
                json={
                    "id": 123,
                    "login": "octocat",
                    "name": "The Octocat",
                    "email": None,
                    "avatar_url": "https://avatars.example/octocat.png",
                },
            )
        if request.url.path == "/user/emails":
            return httpx.Response(
                200,
                json=[
                    {
                        "email": "octocat@example.com",
                        "primary": True,
                        "verified": True,
                    }
                ],
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubOAuthClient(
            client_id="client-id",
            client_secret="client-secret",
            callback_url="http://localhost/callback",
            http_client=http_client,
        )
        token = await client.exchange_code("oauth-code")
        profile = await client.get_user(token.access_token)

    assert token.access_token == "token"
    assert profile.login == "octocat"
    assert profile.email == "octocat@example.com"


@pytest.mark.asyncio
async def test_load_repositories_and_branches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/user/repos":
            return httpx.Response(200, json=[{
                "id": 42,
                "name": "guardian",
                "full_name": "octocat/guardian",
                "owner": {"login": "octocat"},
                "private": True,
                "visibility": "private",
                "html_url": "https://github.com/octocat/guardian",
                "default_branch": "main",
                "updated_at": "2026-06-21T12:00:00Z",
            }])
        if request.url.path == "/repos/octocat/guardian/branches":
            return httpx.Response(200, json=[{"name": "main"}, {"name": "develop"}])
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubOAuthClient("id", "secret", "callback", http_client)
        repositories = await client.list_repositories("token")
        branches = await client.list_branches("token", repositories[0].full_name)

    assert repositories[0].id == 42
    assert repositories[0].private is True
    assert [branch.name for branch in branches] == ["main", "develop"]


@pytest.mark.asyncio
async def test_loads_workflow_jobs_and_log_archive() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jobs"):
            return httpx.Response(200, json={"jobs": [{
                "id": 99,
                "name": "test",
                "status": "completed",
                "conclusion": "failure",
                "started_at": "2026-06-22T10:00:00Z",
                "completed_at": "2026-06-22T10:01:00Z",
                "runner_name": "GitHub Actions 1",
                "html_url": "https://github.com/octocat/guardian/actions/runs/42/job/99",
                "steps": [
                    {
                        "name": "Run tests",
                        "status": "completed",
                        "conclusion": "failure",
                        "number": 1,
                        "started_at": "2026-06-22T10:00:00Z",
                        "completed_at": "2026-06-22T10:01:00Z",
                    }
                ],
            }]})
        if request.url.path.endswith("/logs"):
            return httpx.Response(200, content=b"zip-content")
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubOAuthClient("id", "secret", "callback", http_client)
        jobs = await client.list_workflow_jobs("token", "octocat/guardian", 42)
        logs = await client.download_workflow_logs("token", "octocat/guardian", 42)

    assert jobs[0].conclusion == "failure"
    assert jobs[0].steps[0].name == "Run tests"
    assert logs == b"zip-content"


@pytest.mark.asyncio
async def test_requests_workflow_and_job_reruns() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer installation-token"
        requested_paths.append(request.url.path)
        return httpx.Response(201)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubOAuthClient("id", "secret", "callback", http_client)
        await client.rerun_workflow(
            "installation-token", "octocat/guardian", 42, failed_jobs_only=True
        )
        await client.rerun_job("installation-token", "octocat/guardian", 99)

    assert requested_paths == [
        "/repos/octocat/guardian/actions/runs/42/rerun-failed-jobs",
        "/repos/octocat/guardian/actions/jobs/99/rerun",
    ]
