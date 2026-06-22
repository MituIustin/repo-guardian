from pydantic import SecretStr

from app.core.config import Settings, get_settings


def test_rejects_webhook_with_invalid_signature(client) -> None:
    app = client.app
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url="postgresql+asyncpg://repo_guardian:test@localhost/repo_guardian_test",
        github_webhook_secret=SecretStr("test-secret"),
    )

    response = client.post(
        "/api/webhooks/github",
        content=b"{}",
        headers={
            "X-GitHub-Event": "workflow_run",
            "X-GitHub-Delivery": "delivery-id",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "The GitHub webhook signature is invalid."}
