import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.common.errors import AppError, NotConfiguredError
from app.config import Settings, get_settings
from app.github_integration.connection_dependencies import get_connection_service
from app.github_integration.schemas import ConnectionStatusResponse
from app.github_integration.service import ConnectionService
from app.identity.dependencies import get_current_user, get_optional_current_user
from app.identity.schemas import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])

INSTALL_COOKIE = "devpulse_install"
INSTALL_COOKIE_PATH = "/api/github"

# Only these codes ever reach the browser's URL, so an error can never carry
# arbitrary text. The frontend maps each one to a fixed message.
CONNECT_ERROR_CODES = {
    "invalid_state",
    "installation_not_allowed",
    "github_unavailable",
    "not_configured",
    "failed",
}


def _redirect(settings: Settings, path: str, error: str | None = None) -> RedirectResponse:
    safe_error = None
    if error is not None:
        safe_error = error if error in CONNECT_ERROR_CODES else "failed"
    suffix = f"?error={safe_error}" if safe_error else ""
    response = RedirectResponse(f"{settings.frontend_origin}{path}{suffix}", status_code=302)
    response.delete_cookie(INSTALL_COOKIE, path=INSTALL_COOKIE_PATH)
    return response


def _connect_redirect(settings: Settings, error: str | None = None) -> RedirectResponse:
    return _redirect(settings, "/connect", error)


@router.get("/connection", response_model=ConnectionStatusResponse)
async def read_connection_status(
    user: CurrentUser = Depends(get_current_user),
    service: ConnectionService = Depends(get_connection_service),
) -> ConnectionStatusResponse:
    return await service.get_status(user)


@router.get("/install")
async def start_github_install(
    user: CurrentUser = Depends(get_optional_current_user),
    service: ConnectionService = Depends(get_connection_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if user is None:
        return RedirectResponse(f"{settings.frontend_origin}/sign-in", status_code=302)
    try:
        start = await service.start_install(user)
    except NotConfiguredError:
        return _connect_redirect(settings, "not_configured")
    response = RedirectResponse(start.url, status_code=302)
    response.set_cookie(
        INSTALL_COOKIE,
        start.nonce,
        max_age=settings.oauth_state_ttl_minutes * 60,
        path=INSTALL_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@router.get("/install/callback")
async def finish_github_install(
    request: Request,
    installation_id: str | None = None,
    setup_action: str | None = None,
    state: str | None = None,
    user: CurrentUser = Depends(get_optional_current_user),
    service: ConnectionService = Depends(get_connection_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if user is None:
        return RedirectResponse(f"{settings.frontend_origin}/sign-in", status_code=302)
    try:
        connection = await service.complete_install(
            user=user,
            installation_id=installation_id,
            state=state,
            nonce=request.cookies.get(INSTALL_COOKIE),
            setup_action=setup_action,
        )
    except AppError as exc:
        # The browser only gets a short code, so record it for tracing.
        logger.warning("install callback rejected", extra={"code": exc.code})
        return _connect_redirect(settings, exc.code)
    except Exception:
        # A browser navigation cannot show JSON, so send the user back with a
        # generic message. The details stay in the (redacted) server log.
        logger.exception("install callback failed unexpectedly")
        return _connect_redirect(settings, "failed")
    # A healthy connection goes straight on to choosing repositories; one that needs
    # attention stays on the connect page, which explains what to fix.
    if connection.status == "active":
        return _redirect(settings, "/repositories")
    return _connect_redirect(settings)
