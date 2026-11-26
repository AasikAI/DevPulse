import uuid

from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    """The signed-in user as other modules see it (not an ORM object)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    github_user_id: int
    login: str
    name: str | None
    avatar_url: str | None
    email: str | None


class UserResponse(BaseModel):
    """What `GET /api/auth/me` returns. No GitHub-side identifiers or credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    login: str
    name: str | None
    avatar_url: str | None
    email: str | None
