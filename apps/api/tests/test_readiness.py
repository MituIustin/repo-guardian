from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.core.database import get_db_session
from app.main import app


class AvailableSession:
    async def execute(self, _statement) -> None:
        return None


class UnavailableSession:
    async def execute(self, _statement) -> None:
        raise ConnectionError("Database is unavailable")


def override_session(session) -> None:
    async def dependency() -> AsyncIterator[object]:
        yield session

    app.dependency_overrides[get_db_session] = dependency


def test_readiness_reports_available_database(client: TestClient) -> None:
    override_session(AvailableSession())

    response = client.get("/api/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"] == {"database": "ok"}
    app.dependency_overrides.clear()


def test_readiness_hides_database_error_details(client: TestClient) -> None:
    override_session(UnavailableSession())

    response = client.get("/api/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"] == {"database": "unavailable"}
    assert "Database is unavailable" not in response.text
    app.dependency_overrides.clear()

