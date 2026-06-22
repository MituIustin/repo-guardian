from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.auth.dependencies import get_github_oauth_client
from app.core.database import get_db_session
from app.main import app


class FakeGitHubClient:
    def authorization_url(self, state: str) -> str:
        return f"https://github.example/authorize?state={state}"


class EmptySession:
    async def get(self, _model, _identifier):
        return None


async def empty_session() -> AsyncIterator[EmptySession]:
    yield EmptySession()


def test_github_login_sets_state_and_redirects(client: TestClient) -> None:
    app.dependency_overrides[get_github_oauth_client] = lambda: FakeGitHubClient()

    response = client.get("/api/auth/github/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://github.example/authorize?state=")
    assert "repo_guardian_session=" in response.headers["set-cookie"]


def test_callback_rejects_missing_oauth_state(client: TestClient) -> None:
    app.dependency_overrides[get_github_oauth_client] = lambda: FakeGitHubClient()
    app.dependency_overrides[get_db_session] = empty_session

    response = client.get(
        "/api/auth/github/callback?code=oauth-code&state=unexpected",
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "GitHub OAuth state is invalid or expired."


def test_current_user_requires_authenticated_session(client: TestClient) -> None:
    app.dependency_overrides[get_db_session] = empty_session

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated."


def test_logout_clears_session(client: TestClient) -> None:
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
