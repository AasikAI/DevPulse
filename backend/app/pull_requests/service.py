import uuid
from collections.abc import Callable
from datetime import datetime

from app.common.clock import utcnow
from app.github_integration.schemas import GitHubPullRequestInfo
from app.pull_requests.repository import PullRequestRepository
from app.pull_requests.schemas import PendingReview


class PullRequestService:
    def __init__(
        self,
        *,
        repository: PullRequestRepository,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def stage_page(
        self, *, repository_id: uuid.UUID, pull_requests: list[GitHubPullRequestInfo]
    ) -> None:
        """Store one page of pull requests without committing.

        The caller commits together with the repository's progress cursor, so a
        page and its cursor are saved as one unit.
        """
        await self._repository.upsert_many(
            repository_id=repository_id, pull_requests=pull_requests, now=self._clock()
        )

    async def reviews_backlog(
        self, *, repository_id: uuid.UUID, limit: int
    ) -> list[PendingReview]:
        rows = await self._repository.reviews_backlog(repository_id=repository_id, limit=limit)
        return [PendingReview.model_validate(row) for row in rows]

    async def save_review_state(
        self, *, pull_request_id: uuid.UUID, review_state: str, loaded_for: datetime
    ) -> None:
        await self._repository.set_review_state(
            pull_request_id=pull_request_id, review_state=review_state, loaded_for=loaded_for
        )
        await self._repository.commit()
