import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GithubRepository(Base):
    """A repository the App can access. Identity only; never source code."""

    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("connection_id", "github_repo_id", name="uq_repositories_connection_repo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("github_connections.id", ondelete="CASCADE"), index=True
    )
    # GitHub's numeric ID survives renames and transfers; full_name does not.
    github_repo_id: Mapped[int] = mapped_column(BigInteger)
    owner_login: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(511))
    is_private: Mapped[bool] = mapped_column(Boolean)
    # False once the App can no longer see the repository. The row is kept.
    is_available: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
