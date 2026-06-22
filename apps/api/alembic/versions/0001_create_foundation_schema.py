"""Create the initial Repo Guardian foundation schema.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "repositories",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("github_repository_id", sa.BigInteger(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(511), nullable=False),
        sa.Column("default_branch", sa.String(255), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False),
        sa.Column("html_url", sa.String(2048), nullable=False),
        *timestamp_columns(),
        sa.UniqueConstraint("github_repository_id", name="uq_repositories_github_repository_id"),
        sa.UniqueConstraint("full_name", name="uq_repositories_full_name"),
    )

    op.create_table(
        "github_accounts",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("github_user_id", name="uq_github_accounts_github_user_id"),
    )
    op.create_index("ix_github_accounts_user_id", "github_accounts", ["user_id"])
    op.create_index("ix_github_accounts_username", "github_accounts", ["username"])

    op.create_table(
        "workflow_runs",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("repository_id", uuid_type, nullable=False),
        sa.Column("github_run_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_id", sa.BigInteger(), nullable=True),
        sa.Column("workflow_name", sa.String(255), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("run_attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("branch", sa.String(255), nullable=False),
        sa.Column("commit_sha", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("conclusion", sa.String(32), nullable=True),
        sa.Column("trigger_event", sa.String(64), nullable=False),
        sa.Column("html_url", sa.String(2048), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("github_run_id", name="uq_workflow_runs_github_run_id"),
    )
    op.create_index("ix_workflow_runs_repository_id", "workflow_runs", ["repository_id"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])
    op.create_index("ix_workflow_runs_conclusion", "workflow_runs", ["conclusion"])

    op.create_table(
        "build_jobs",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_run_id", uuid_type, nullable=False),
        sa.Column("github_job_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("conclusion", sa.String(32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runner_name", sa.String(255), nullable=True),
        sa.Column("html_url", sa.String(2048), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("github_job_id", name="uq_build_jobs_github_job_id"),
    )
    op.create_index("ix_build_jobs_workflow_run_id", "build_jobs", ["workflow_run_id"])

    op.create_table(
        "incidents",
        sa.Column("id", uuid_type, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("repository_id", uuid_type, nullable=False),
        sa.Column("workflow_run_id", uuid_type, nullable=False),
        sa.Column("failed_job_id", uuid_type, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_incidents_confidence_range",
        ),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["failed_job_id"], ["build_jobs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_incidents_repository_id", "incidents", ["repository_id"])
    op.create_index("ix_incidents_workflow_run_id", "incidents", ["workflow_run_id"])
    op.create_index("ix_incidents_failed_job_id", "incidents", ["failed_job_id"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_category", "incidents", ["category"])


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("build_jobs")
    op.drop_table("workflow_runs")
    op.drop_table("github_accounts")
    op.drop_table("repositories")
    op.drop_table("users")
