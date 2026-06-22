"""Add webhook delivery and build log excerpt persistence.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repository_connections",
        sa.Column(
            "webhook_status",
            sa.String(length=32),
            nullable=False,
            server_default="not_configured",
        ),
    )
    op.add_column(
        "repository_connections",
        sa.Column("webhook_last_received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "webhook_deliveries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("github_delivery_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signature_verified", sa.Boolean(), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["repository_id"], ["repositories.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_webhook_deliveries_repository_id", "webhook_deliveries", ["repository_id"]
    )
    op.create_index(
        "ix_webhook_deliveries_processing_status",
        "webhook_deliveries",
        ["processing_status"],
    )
    op.create_table(
        "build_log_excerpts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("build_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_file", sa.String(length=1024), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["build_job_id"], ["build_jobs.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_build_log_excerpts_workflow_run_id",
        "build_log_excerpts",
        ["workflow_run_id"],
    )
    op.create_index(
        "ix_build_log_excerpts_build_job_id", "build_log_excerpts", ["build_job_id"]
    )


def downgrade() -> None:
    op.drop_table("build_log_excerpts")
    op.drop_table("webhook_deliveries")
    op.drop_column("repository_connections", "webhook_last_received_at")
    op.drop_column("repository_connections", "webhook_status")
