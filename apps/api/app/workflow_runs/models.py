import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    github_run_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    workflow_id: Mapped[int | None] = mapped_column(BigInteger)
    workflow_name: Mapped[str] = mapped_column(String(255))
    run_number: Mapped[int] = mapped_column(Integer)
    run_attempt: Mapped[int] = mapped_column(Integer, default=1)
    branch: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    conclusion: Mapped[str | None] = mapped_column(String(32), index=True)
    trigger_event: Mapped[str] = mapped_column(String(64))
    html_url: Mapped[str] = mapped_column(String(2048))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

