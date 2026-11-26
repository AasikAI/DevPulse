import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GitHubUser(BaseModel):
    """The few fields DevPulse keeps from GitHub's `GET /user` response."""

    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None
    # Null when the user has no public email.
    email: str | None = None


class GitHubInstallation(BaseModel):
    """What DevPulse keeps from `GET /app/installations/{id}`."""

    id: int
    account_id: int
    account_login: str
    account_type: str
    permissions: dict[str, str] = Field(default_factory=dict)
    suspended: bool = False


class GitHubRepositoryInfo(BaseModel):
    """One repository the App can access. No source code, only identity."""

    id: int
    name: str
    full_name: str
    owner_login: str
    is_private: bool


ConnectionStatus = Literal["not_connected", "active", "needs_attention"]


class ConnectionInfo(BaseModel):
    """A connection as other modules see it (not an ORM object)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    installation_id: int
    github_account_login: str
    status: str
    status_reason: str | None
    created_at: datetime
    last_checked_at: datetime | None
    repositories_synced_at: datetime | None


class ConnectionStatusResponse(BaseModel):
    """What `GET /api/github/connection` returns. No installation IDs or credentials."""

    status: ConnectionStatus
    reason: str | None = None
    account_login: str | None = None
    connected_at: datetime | None = None
    last_checked_at: datetime | None = None
    repositories_synced_at: datetime | None = None
    repository_count: int = 0
