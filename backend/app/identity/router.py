import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.common.errors import AppError, NotConfiguredError
from app.config import Settings, get_settings
from app.identity.dependencies import (
    OAUTH_COOKIE,
    SESSION_COOKIE,
    get_current_user,
    get_identity_service,
)
from app.identity.errors import SignInCancelledError
from app.identity.schemas import CurrentUser, UserResponse
from app.identity.service import IdentityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Only these codes ever reach the browser's URL, so an error can never carry
# arbitrary text. The frontend maps each one to a fixed message.
SIGN_IN_ERROR_CODES = {
    "cancelled",
    "invalid_state",
    "github_unavailable",
    "not_configured",
    "failed",
}

OAUTH_COOKIE_PATH = "/api/auth"


def _sign_in_error_redirect(settings: Settings, code: str) -> RedirectResponse:
    safe_code = code if code in SIGN_IN_ERROR_CODES else "failed"
    response = RedirectResponse(
        f"{settings.frontend_origin}/sign-in?error={safe_code}", status_code=302
    )
    response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH)
    return response


@router.get("/github/login")
async def start_github_sign_in(
    service: IdentityService = Depends(get_identity_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    try:
        start = await service.start_sign_in()
    except NotConfiguredError:
        return _sign_in_error_redirect(settings, "not_configured")
    response = RedirectResponse(start.authorize_url, status_code=302)
    response.set_cookie(
        OAUTH_COOKIE,
        start.nonce,
        max_age=settings.oauth_state_ttl_minutes * 60,
        path=OAUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@router.get("/github/callback")
async def finish_github_sign_in(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    service: IdentityService = Depends(get_identity_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    try:
        if error:
            raise SignInCancelledError()
        result = await service.complete_sign_in(
            code=code,
            state=state,
            nonce=request.cookies.get(OAUTH_COOKIE),
            previous_session_token=request.cookies.get(SESSION_COOKIE),
        )
    except AppError as exc:
        return _sign_in_error_redirect(settings, exc.code)
    except Exception:
        # A browser navigation cannot show JSON, so send the user back with a
        # generic message. The details stay in the (redacted) server log.
        logger.exception("sign-in callback failed unexpectedly")
        return _sign_in_error_redirect(settings, "failed")

    response = RedirectResponse(f"{settings.frontend_origin}/start", status_code=302)
    response.delete_cookie(OAUTH_COOKIE, path=OAUTH_COOKIE_PATH)
    response.set_cookie(
        SESSION_COOKIE,
        result.session_token,
        max_age=settings.session_lifetime_days * 24 * 60 * 60,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@router.get("/me", response_model=UserResponse)
async def read_current_user(user: CurrentUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=204)
async def log_out(
    request: Request,
    service: IdentityService = Depends(get_identity_service),
    settings: Settings = Depends(get_settings),
) -> Response:
    await service.sign_out(request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=settings.cookie_secure, samesite="lax"
    )
    return response
