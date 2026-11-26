import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PendingReview(BaseModel):
    """A pull request whose review state is not loaded yet, or is out of date."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    state: str
    updated_at_gh: datetime


class WeeklyCount(BaseModel):
    """Pull requests opened and merged in one UTC week (Monday to Sunday)."""

    week_start: date
    opened: int
    merged: int


class PullRequestTotals(BaseModel):
    open_now: int
    opened_in_window: int
    merged_in_window: int


class ReviewStateCounts(BaseModel):
    """Open pull requests by review state. `not_loaded` means the review pass has not reached them yet."""

    none: int = 0
    commented: int = 0
    approved: int = 0
    changes_requested: int = 0
    not_loaded: int = 0


class PullRequestSummaryResponse(BaseModel):
    """Everything the dashboard widget shows, read from the database. No people, no GitHub IDs."""

    connection_status: Literal["not_connected", "active", "needs_attention"]
    connection_reason: str | None
    # Selected repositories the App can still access.
    repository_count: int
    weeks: int
    # The Monday of the first week in `weekly`; every week is UTC.
    window_start: date
    last_updated_at: datetime | None
    is_stale: bool
    stale_reason: Literal["last_run_failed", "not_updated_recently"] | None
    # False while any selected repository's history import is unfinished.
    history_complete: bool
    history_repositories_total: int
    history_repositories_complete: int
    totals: PullRequestTotals
    open_by_review_state: ReviewStateCounts
    weekly: list[WeeklyCount]
