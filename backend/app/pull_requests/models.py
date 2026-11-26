import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PullRequest(Base):
    """A pull request of a selected repository.

    Only what the dashboard needs: state, review state and key dates, plus the
    title, author and branch name for display. No bodies, comments or code.
    """

    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repository_id", "number", name="uq_pull_requests_repository_number"),
        Index("ix_pull_requests_repository_created", "repository_id", "created_at_gh"),
        Index("ix_pull_requests_repository_merged", "repository_id", "merged_at"),
        Index("ix_pull_requests_repository_state", "repository_id", "state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE")
    )
    github_pr_id: Mapped[int] = mapped_column(BigInteger)
    number: Mapped[int] = mapped_column(Integer)
    # open | closed (not merged) | merged
    state: Mapped[str] = mapped_column(String(16))
    is_draft: Mapped[bool] = mapped_column(Boolean)
    title: Mapped[str] = mapped_column(String(1024))
    author_login: Mapped[str | None] = mapped_column(String(255))
    head_branch: Mapped[str | None] = mapped_column(String(255))
    # none | commented | approved | changes_requested. Null until the review pass reaches it.
    review_state: Mapped[str | None] = mapped_column(String(32))
    # The pull request's updated_at at the time its reviews were read. A newer updated_at
    # means the reviews should be read again.
    reviews_loaded_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at_gh: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at_gh: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
