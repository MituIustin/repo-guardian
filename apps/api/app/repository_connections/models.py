import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class RepositoryConnection(TimestampMixin, Base):
    __tablename__ = "repository_connections"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "repository_id", name="uq_repository_connections_user_repository"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    github_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    installation_id: Mapped[int | None] = mapped_column(BigInteger)
    monitored_branch: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_status: Mapped[str] = mapped_column(String(32), default="not_configured")
    webhook_last_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
