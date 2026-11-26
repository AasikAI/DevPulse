from pydantic import BaseModel


class GitHubUser(BaseModel):
    """The few fields DevPulse keeps from GitHub's `GET /user` response."""

    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None
    # Null when the user has no public email.
    email: str | None = None
