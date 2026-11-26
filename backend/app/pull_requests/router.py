from fastapi import APIRouter, Depends, Query

from app.identity.dependencies import get_current_user
from app.identity.schemas import CurrentUser
from app.pull_requests.dependencies import get_summary_service
from app.pull_requests.schemas import PullRequestSummaryResponse
from app.pull_requests.summary_service import PullRequestSummaryService

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])

DEFAULT_WEEKS = 12
MAX_WEEKS = 52


@router.get("/summary", response_model=PullRequestSummaryResponse)
async def read_pull_request_summary(
    weeks: int = Query(default=DEFAULT_WEEKS, ge=1, le=MAX_WEEKS),
    user: CurrentUser = Depends(get_current_user),
    service: PullRequestSummaryService = Depends(get_summary_service),
) -> PullRequestSummaryResponse:
    return await service.summarize(user, weeks=weeks)
