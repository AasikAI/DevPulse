from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import NotAuthenticatedError
from app.config import Settings, get_settings
from app.db import get_db
from app.github_integration.client import GitHubClient
from app.github_integration.dependencies import get_github_client
from app.identity.repository import IdentityRepository
from app.identity.schemas import CurrentUser
from app.identity.service import IdentityService

SESSION_COOKIE = "devpulse_session"
OAUTH_COOKIE = "devpulse_oauth"


def get_identity_service(
    db: AsyncSession = Depends(get_db),
    github: GitHubClient = Depends(get_github_client),
    settings: Settings = Depends(get_settings),
) -> IdentityService:
    return IdentityService(
        repository=IdentityRepository(db), github=github, settings=settings
    )


async def get_current_user(
    request: Request, service: IdentityService = Depends(get_identity_service)
) -> CurrentUser:
    """Protects a route: 401 unless the session cookie maps to an active session."""
    return await service.authenticate(request.cookies.get(SESSION_COOKIE))


async def get_optional_current_user(
    request: Request, service: IdentityService = Depends(get_identity_service)
) -> CurrentUser | None:
    """For browser redirects, where a JSON 401 would be a dead end."""
    try:
        return await service.authenticate(request.cookies.get(SESSION_COOKIE))
    except NotAuthenticatedError:
        return None
