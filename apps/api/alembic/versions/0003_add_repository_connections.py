"""Add user repository connections.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repository_connections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=True),
        sa.Column("monitored_branch", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["repository_id"], ["repositories.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["github_account_id"], ["github_accounts.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "user_id", "repository_id", name="uq_repository_connections_user_repository"
        ),
    )
    op.create_index(
        "ix_repository_connections_user_id", "repository_connections", ["user_id"]
    )
    op.create_index(
        "ix_repository_connections_repository_id",
        "repository_connections",
        ["repository_id"],
    )
    op.create_index(
        "ix_repository_connections_github_account_id",
        "repository_connections",
        ["github_account_id"],
    )


def downgrade() -> None:
    op.drop_table("repository_connections")

