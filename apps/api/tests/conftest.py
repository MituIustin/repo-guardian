"""Shared API test configuration."""

# ruff: noqa: E402

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://repo_guardian:local-test@localhost:5432/repo_guardian_test",
)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
