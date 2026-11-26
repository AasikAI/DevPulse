import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GithubConnection(Base):
    """A user's installation of the DevPulse GitHub App. One per user."""

    __tablename__ = "github_connections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    installation_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    github_account_id: Mapped[int] = mapped_column(BigInteger)
    github_account_login: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(32))
    permissions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    # active | needs_attention
    status: Mapped[str] = mapped_column(String(32), server_default="active")
    # access_revoked | permission_missing | suspended (set with needs_attention)
    status_reason: Mapped[str | None] = mapped_column(String(64))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Null until the first repository list has been fetched.
    repositories_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The last pull request sync run that finished without failing (complete or partial).
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # GitHub's rate limit is used up until this moment; the schedule skips the connection.
    rate_limited_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
