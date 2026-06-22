"""Add encrypted GitHub OAuth credential fields.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "github_accounts",
        sa.Column("access_token_encrypted", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "github_accounts",
        sa.Column("token_scope", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "github_accounts",
        sa.Column("token_type", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_accounts", "token_type")
    op.drop_column("github_accounts", "token_scope")
    op.drop_column("github_accounts", "access_token_encrypted")

