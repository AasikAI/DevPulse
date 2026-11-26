import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_CHANGES_PER_REQUEST = 500


class SyncRepository(BaseModel):
    """A selected repository as the background sync sees it, with its import progress."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    backfill_cursor: int
    backfill_started_at: datetime | None
    backfill_completed_at: datetime | None
    incremental_watermark: datetime | None
    last_synced_at: datetime | None


class RepositoryItem(BaseModel):
    """One repository in the selection list. No GitHub IDs or connection details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    is_private: bool
    is_selected: bool


class RepositoryListResponse(BaseModel):
    # syncing: the first repository list has not been fetched yet.
    list_status: Literal["syncing", "ready"]
    refreshed_at: datetime | None
    # Repositories matching the search, across all pages.
    total: int
    # Selected repositories overall, regardless of the search or page.
    selected_count: int
    page: int
    page_size: int
    items: list[RepositoryItem]


class SelectionRequest(BaseModel):
    """Changes to apply: deltas, so they work with a paginated list."""

    select: list[uuid.UUID] = Field(default_factory=list, max_length=MAX_CHANGES_PER_REQUEST)
    unselect: list[uuid.UUID] = Field(default_factory=list, max_length=MAX_CHANGES_PER_REQUEST)

    @model_validator(mode="after")
    def _no_contradictions(self) -> "SelectionRequest":
        if set(self.select) & set(self.unselect):
            raise ValueError("a repository cannot be both selected and unselected")
        return self


class SelectionResponse(BaseModel):
    selected_count: int
