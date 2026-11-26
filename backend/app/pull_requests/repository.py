import uuid
from datetime import datetime

from sqlalchemy import case, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.github_integration.schemas import GitHubPullRequestInfo
from app.pull_requests.models import PullRequest


class PullRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_many(
        self,
        *,
        repository_id: uuid.UUID,
        pull_requests: list[GitHubPullRequestInfo],
        now: datetime,
    ) -> None:
        """Insert new pull requests and refresh changed ones; safe to run twice.

        Review state is not touched here: it is filled in by the review pass, and a
        newer `updated_at_gh` is what marks it for a re-read.
        """
        if not pull_requests:
            return
        statement = pg_insert(PullRequest).values(
            [
                {
                    "id": uuid.uuid4(),
                    "repository_id": repository_id,
                    "github_pr_id": pr.id,
                    "number": pr.number,
                    "state": pr.state,
                    "is_draft": pr.is_draft,
                    "title": pr.title,
                    "author_login": pr.author_login,
                    "head_branch": pr.head_branch,
                    "created_at_gh": pr.created_at,
                    "updated_at_gh": pr.updated_at,
                    "closed_at": pr.closed_at,
                    "merged_at": pr.merged_at,
                    "fetched_at": now,
                }
                for pr in pull_requests
            ]
        )
        statement = statement.on_conflict_do_update(
            constraint="uq_pull_requests_repository_number",
            set_={
                "github_pr_id": statement.excluded.github_pr_id,
                "state": statement.excluded.state,
                "is_draft": statement.excluded.is_draft,
                "title": statement.excluded.title,
                "author_login": statement.excluded.author_login,
                "head_branch": statement.excluded.head_branch,
                "created_at_gh": statement.excluded.created_at_gh,
                "updated_at_gh": statement.excluded.updated_at_gh,
                "closed_at": statement.excluded.closed_at,
                "merged_at": statement.excluded.merged_at,
                "fetched_at": now,
            },
        )
        await self._db.execute(statement)

    async def reviews_backlog(
        self, *, repository_id: uuid.UUID, limit: int
    ) -> list[PullRequest]:
        """Pull requests that need their reviews read: open ones first, then the newest."""
        result = await self._db.execute(
            select(PullRequest)
            .where(
                PullRequest.repository_id == repository_id,
                or_(
                    PullRequest.reviews_loaded_for.is_(None),
                    PullRequest.reviews_loaded_for < PullRequest.updated_at_gh,
                ),
            )
            .order_by(
                case((PullRequest.state == "open", 0), else_=1),
                PullRequest.updated_at_gh.desc(),
                PullRequest.number.desc(),
            )
            .limit(limit)
        )
        return list(result.scalars())

    async def set_review_state(
        self, *, pull_request_id: uuid.UUID, review_state: str, loaded_for: datetime
    ) -> None:
        await self._db.execute(
            update(PullRequest)
            .where(PullRequest.id == pull_request_id)
            .values(review_state=review_state, reviews_loaded_for=loaded_for)
        )

    async def commit(self) -> None:
        await self._db.commit()
