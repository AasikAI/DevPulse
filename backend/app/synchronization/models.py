import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SyncRun(Base):
    """One background job run, kept so the app can show state and failures safely."""

    __tablename__ = "sync_runs"
    __table_args__ = (
        # At most one running job per connection: the guard against duplicate delivery.
        Index(
            "uq_sync_runs_one_running_per_connection",
            "connection_id",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
        Index("ix_sync_runs_connection_started", "connection_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("github_connections.id", ondelete="CASCADE")
    )
    # repository_list (pull_requests arrives with the pull request sync)
    kind: Mapped[str] = mapped_column(String(32))
    # connected | selection_saved | schedule
    trigger: Mapped[str] = mapped_column(String(32))
    # running | succeeded | failed | rate_limited
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # A fixed category such as github_unavailable; never raw error text.
    error_category: Mapped[str | None] = mapped_column(String(64))
