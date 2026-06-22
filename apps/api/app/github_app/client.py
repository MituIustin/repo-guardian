import base64
import json
import time

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.github.client import GITHUB_API_VERSION, GitHubOAuthError
from app.github.schemas import GitHubRepository
from app.github_app.schemas import GitHubInstallation, InstallationToken


class GitHubAppConfigurationError(ValueError):
    """Raised when GitHub App credentials cannot be loaded."""


class GitHubAppClient:
    def __init__(
        self,
        app_id: int,
        private_key_base64: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.app_id = app_id
        self.http_client = http_client
        try:
            key_bytes = base64.b64decode(private_key_base64, validate=True)
            self.private_key = serialization.load_pem_private_key(
                key_bytes, password=None
            )
            if not isinstance(self.private_key, rsa.RSAPrivateKey):
                raise ValueError("Expected an RSA private key")
        except (TypeError, ValueError) as error:
            raise GitHubAppConfigurationError(
                "The GitHub App private key is invalid"
            ) from error

    def create_jwt(self, now: int | None = None) -> str:
        issued_at = (now or int(time.time())) - 60
        header = self._encode({"alg": "RS256", "typ": "JWT"})
        payload = self._encode(
            {"iat": issued_at, "exp": issued_at + 600, "iss": str(self.app_id)}
        )
        signing_input = f"{header}.{payload}".encode("ascii")
        signature = self.private_key.sign(
            signing_input, padding.PKCS1v15(), hashes.SHA256()
        )
        return f"{header}.{payload}.{self._encode_bytes(signature)}"

    async def get_installation(self, installation_id: int) -> GitHubInstallation:
        response = await self._request(
            "GET",
            f"https://api.github.com/app/installations/{installation_id}",
            headers=self._app_headers(),
        )
        try:
            return GitHubInstallation.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError("GitHub returned an invalid installation") from error

    async def create_installation_token(self, installation_id: int) -> InstallationToken:
        response = await self._request(
            "POST",
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=self._app_headers(),
        )
        try:
            return InstallationToken.model_validate(response.json())
        except (TypeError, ValueError) as error:
            raise GitHubOAuthError(
                "GitHub returned an invalid installation token"
            ) from error

    async def delete_installation(self, installation_id: int) -> None:
        await self._request(
            "DELETE",
            f"https://api.github.com/app/installations/{installation_id}",
            headers=self._app_headers(),
        )

    async def list_installation_repositories(
        self, installation_id: int
    ) -> list[GitHubRepository]:
        token = await self.create_installation_token(installation_id)
        repositories: list[GitHubRepository] = []
        page = 1
        while True:
            response = await self._request(
                "GET",
                "https://api.github.com/installation/repositories",
                headers=self._installation_headers(token.token),
                params={"per_page": 100, "page": page},
            )
            try:
                payload = response.json()
                items = payload.get("repositories") if isinstance(payload, dict) else None
                if not isinstance(items, list):
                    raise TypeError("Expected repositories")
                repositories.extend(
                    GitHubRepository.model_validate(item) for item in items
                )
            except (TypeError, ValueError) as error:
                raise GitHubOAuthError(
                    "GitHub returned invalid installation repositories"
                ) from error
            if len(items) < 100:
                break
            page += 1
        return repositories

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            if self.http_client is not None:
                response = await self.http_client.request(method, url, **kwargs)
            else:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as error:
            raise GitHubOAuthError("GitHub App request failed") from error

    def _app_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.create_jwt()}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    @staticmethod
    def _installation_headers(token: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    @staticmethod
    def _encode(payload: dict[str, object]) -> str:
        return GitHubAppClient._encode_bytes(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )

    @staticmethod
    def _encode_bytes(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
