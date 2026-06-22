import asyncio
import os
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config

EXPECTED_TABLES = {
    "users",
    "github_accounts",
    "repositories",
    "workflow_runs",
    "build_jobs",
    "incidents",
    "repository_connections",
    "webhook_deliveries",
    "build_log_excerpts",
    "github_app_installations",
}


async def inspect_schema(database_url: str) -> tuple[set[str], dict[str, object]]:
    engine = create_async_engine(database_url)

    async with engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )

        def inspect_contract(sync_connection) -> dict[str, object]:
            inspector = inspect(sync_connection)
            columns = {
                column["name"]: column["nullable"]
                for column in inspector.get_columns("incidents")
            }
            installation_columns = {
                column["name"]: column["nullable"]
                for column in inspector.get_columns("github_app_installations")
            }
            build_job_columns = {
                column["name"]: column["nullable"]
                for column in inspector.get_columns("build_jobs")
            }
            foreign_keys = inspector.get_foreign_keys("incidents")
            unique_constraints = {
                table: {
                    tuple(constraint["column_names"])
                    for constraint in inspector.get_unique_constraints(table)
                }
                for table in EXPECTED_TABLES
            }
            indexes = {
                table: {
                    tuple(index["column_names"])
                    for index in inspector.get_indexes(table)
                    if not index.get("duplicates_constraint")
                }
                for table in EXPECTED_TABLES
            }
            return {
                "failed_job_nullable": columns["failed_job_id"],
                "failed_job_foreign_key": any(
                    key["referred_table"] == "build_jobs"
                    and key["constrained_columns"] == ["failed_job_id"]
                    for key in foreign_keys
                ),
                "monitoring_enabled_nullable": installation_columns[
                    "monitoring_enabled"
                ],
                "steps_nullable": build_job_columns["steps"],
                "unique_constraints": unique_constraints,
                "indexes": indexes,
            }

        schema_contract = await connection.run_sync(inspect_contract)

    await engine.dispose()
    return tables, schema_contract


@pytest.mark.integration
def test_initial_migration_creates_foundation_schema() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for the PostgreSQL migration test")

    api_root = Path(__file__).parents[1]
    config = Config(api_root / "alembic.ini")
    config.set_main_option("script_location", str(api_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    try:
        tables, contract = asyncio.run(inspect_schema(database_url))
        assert tables == EXPECTED_TABLES | {"alembic_version"}
        assert contract["failed_job_nullable"] is True
        assert contract["failed_job_foreign_key"] is True
        assert contract["monitoring_enabled_nullable"] is False
        assert contract["steps_nullable"] is False

        unique_constraints = contract["unique_constraints"]
        assert ("email",) in unique_constraints["users"]
        assert ("github_user_id",) in unique_constraints["github_accounts"]
        assert ("github_repository_id",) in unique_constraints["repositories"]
        assert ("full_name",) in unique_constraints["repositories"]
        assert ("github_run_id",) in unique_constraints["workflow_runs"]
        assert ("github_job_id",) in unique_constraints["build_jobs"]
        assert ("user_id", "repository_id") in unique_constraints["repository_connections"]
        assert ("github_installation_id",) in unique_constraints[
            "github_app_installations"
        ]

        indexes = contract["indexes"]
        assert ("user_id",) in indexes["github_accounts"]
        assert ("repository_id",) in indexes["workflow_runs"]
        assert ("workflow_run_id",) in indexes["build_jobs"]
        assert ("failed_job_id",) in indexes["incidents"]
        assert ("status",) in indexes["incidents"]
        assert ("user_id",) in indexes["repository_connections"]
        assert ("repository_id",) in indexes["repository_connections"]
        assert ("github_account_id",) in indexes["repository_connections"]
        assert ("repository_id",) in indexes["webhook_deliveries"]
        assert ("processing_status",) in indexes["webhook_deliveries"]
        assert ("workflow_run_id",) in indexes["build_log_excerpts"]
        assert ("build_job_id",) in indexes["build_log_excerpts"]
        assert ("user_id",) in indexes["github_app_installations"]
        assert ("status",) in indexes["github_app_installations"]
    finally:
        command.downgrade(config, "base")
