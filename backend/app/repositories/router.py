from fastapi import APIRouter, Depends, Query

from app.identity.dependencies import get_current_user
from app.identity.schemas import CurrentUser
from app.repositories.schemas import (
    RepositoryListResponse,
    SelectionRequest,
    SelectionResponse,
)
from app.repositories.selection_dependencies import get_selection_service
from app.repositories.selection_service import RepositorySelectionService

router = APIRouter(prefix="/repositories", tags=["repositories"])

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: CurrentUser = Depends(get_current_user),
    service: RepositorySelectionService = Depends(get_selection_service),
) -> RepositoryListResponse:
    return await service.list_repositories(user, search=q, page=page, page_size=page_size)


@router.post("/selection", response_model=SelectionResponse)
async def save_selection(
    body: SelectionRequest,
    user: CurrentUser = Depends(get_current_user),
    service: RepositorySelectionService = Depends(get_selection_service),
) -> SelectionResponse:
    return await service.save_selection(user, select=body.select, unselect=body.unselect)
