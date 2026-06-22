from fastapi.testclient import TestClient


def test_health_does_not_require_database(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "repo-guardian-api",
        "version": "0.1.0",
    }

