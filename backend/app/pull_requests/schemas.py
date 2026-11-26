import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PendingReview(BaseModel):
    """A pull request whose review state is not loaded yet, or is out of date."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    state: str
    updated_at_gh: datetime
