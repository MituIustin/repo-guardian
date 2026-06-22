import uuid

from sqlalchemy import BigInteger, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class GitHubAccount(TimestampMixin, Base):
    __tablename__ = "github_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    github_user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    access_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    token_scope: Mapped[str | None] = mapped_column(String(255))
    token_type: Mapped[str | None] = mapped_column(String(32))
