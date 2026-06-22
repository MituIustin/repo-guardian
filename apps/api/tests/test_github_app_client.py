import base64
import json

import httpx
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.github_app.client import GitHubAppClient


def private_key_base64() -> tuple[str, rsa.RSAPrivateKey]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return base64.b64encode(pem).decode("ascii"), key


def decode_segment(value: str) -> dict[str, object]:
    padding_length = (-len(value)) % 4
    return json.loads(base64.urlsafe_b64decode(value + "=" * padding_length))


def test_creates_short_lived_rs256_app_jwt() -> None:
    encoded_key, key = private_key_base64()
    client = GitHubAppClient(12345, encoded_key)

    token = client.create_jwt(now=1_800_000_000)
    header, payload, signature = token.split(".")

    assert decode_segment(header) == {"alg": "RS256", "typ": "JWT"}
    assert decode_segment(payload) == {
        "iat": 1_799_999_940,
        "exp": 1_800_000_540,
        "iss": "12345",
    }
    signature_bytes = base64.urlsafe_b64decode(signature + "=" * ((-len(signature)) % 4))
    key.public_key().verify(
        signature_bytes,
        f"{header}.{payload}".encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )


@pytest.mark.asyncio
async def test_loads_installation_and_repositories() -> None:
    encoded_key, _ = private_key_base64()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/app/installations/77":
            return httpx.Response(200, json={
                "id": 77,
                "account": {"id": 9, "login": "example-org", "type": "Organization"},
                "repository_selection": "all",
                "suspended_at": None,
            })
        if request.url.path == "/app/installations/77/access_tokens":
            return httpx.Response(201, json={
                "token": "installation-token",
                "expires_at": "2026-06-22T14:00:00Z",
            })
        if request.url.path == "/installation/repositories":
            assert request.headers["Authorization"] == "Bearer installation-token"
            return httpx.Response(200, json={"repositories": [{
                "id": 42,
                "name": "guardian",
                "full_name": "example-org/guardian",
                "owner": {"login": "example-org"},
                "private": True,
                "visibility": "private",
                "html_url": "https://github.com/example-org/guardian",
                "default_branch": "main",
                "updated_at": "2026-06-22T12:00:00Z",
            }]})
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubAppClient(12345, encoded_key, http_client)
        installation = await client.get_installation(77)
        repositories = await client.list_installation_repositories(77)

    assert installation.account.login == "example-org"
    assert repositories[0].full_name == "example-org/guardian"


@pytest.mark.asyncio
async def test_deletes_installation_with_app_authentication() -> None:
    encoded_key, _ = private_key_base64()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/app/installations/77"
        assert request.headers["Authorization"].startswith("Bearer ")
        return httpx.Response(204)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubAppClient(12345, encoded_key, http_client)
        await client.delete_installation(77)
