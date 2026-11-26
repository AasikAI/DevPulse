import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import httpx
import jwt
from pydantic import ValidationError

from app.common.errors import NotConfiguredError
from app.github_integration.errors import (
    ACCESS_REVOKED,
    PERMISSION_MISSING,
    SUSPENDED,
    GitHubAccessError,
    GitHubAuthorizationError,
    GitHubRateLimitedError,
    GitHubUnavailableError,
)
from app.github_integration.schemas import GitHubInstallation, GitHubRepositoryInfo, GitHubUser

logger = logging.getLogger(__name__)

GITHUB_WEB_URL = "https://github.com"
GITHUB_API_URL = "https://api.github.com"

# The read-only permissions DevPulse asks each installation token for.
TOKEN_PERMISSIONS = {"metadata": "read", "pull_requests": "read"}
REPOSITORIES_PER_PAGE = 100
# Safety stop for runaway pagination (10,000 repositories).
MAX_REPOSITORY_PAGES = 100
# GitHub allows at most 10 minutes; stay under it and allow for clock drift.
APP_JWT_LIFETIME_SECONDS = 540
APP_JWT_BACKDATE_SECONDS = 60


class GitHubClient:
    """The only place that talks to GitHub.

    User sign-in: the user token returned by `exchange_code` is meant to be used
    once and thrown away, never stored.

    Installation access: the App signs a short-lived JWT with its private key,
    swaps it for a short-lived installation token, and uses that to read data.
    Neither is stored or logged.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        http: httpx.AsyncClient,
        app_id: str = "",
        app_slug: str = "",
        private_key_path: str = "",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http
        self._app_id = app_id
        self._app_slug = app_slug
        self._private_key_path = private_key_path

    @property
    def is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    @property
    def is_app_configured(self) -> bool:
        return bool(
            self._app_id
            and self._app_slug
            and self._private_key_path
            and Path(self._private_key_path).is_file()
        )

    def authorize_url(self, *, state: str, redirect_uri: str) -> str:
        query = urlencode(
            {"client_id": self._client_id, "redirect_uri": redirect_uri, "state": state}
        )
        return f"{GITHUB_WEB_URL}/login/oauth/authorize?{query}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> str:
        """Trade the one-time OAuth code for a user token (kept in memory only)."""
        try:
            response = await self._http.post(
                f"{GITHUB_WEB_URL}/login/oauth/access_token",
                json={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            # Log only the exception type: the message could echo request details.
            logger.warning("github token exchange failed", extra={"error": type(exc).__name__})
            raise GitHubUnavailableError() from None

        if response.status_code >= 500 or response.status_code == 429:
            logger.warning("github token exchange unavailable", extra={"status": response.status_code})
            raise GitHubUnavailableError()

        try:
            body = response.json()
        except ValueError:
            raise GitHubUnavailableError() from None

        token = body.get("access_token") if isinstance(body, dict) else None
        if response.status_code != 200 or not token:
            # GitHub answers 200 with {"error": "bad_verification_code"} for bad codes.
            reason = body.get("error") if isinstance(body, dict) else None
            logger.info("github rejected authorization code", extra={"reason": str(reason)})
            raise GitHubAuthorizationError()
        return token

    async def get_authenticated_user(self, token: str) -> GitHubUser:
        try:
            response = await self._http.get(
                f"{GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        except httpx.HTTPError as exc:
            logger.warning("github user lookup failed", extra={"error": type(exc).__name__})
            raise GitHubUnavailableError() from None

        if response.status_code in (401, 403) and response.headers.get("x-ratelimit-remaining") != "0":
            raise GitHubAuthorizationError()
        if response.status_code >= 400:
            logger.warning("github user lookup unavailable", extra={"status": response.status_code})
            raise GitHubUnavailableError()

        try:
            return GitHubUser.model_validate(response.json())
        except (ValueError, ValidationError):
            logger.warning("github user response was not usable")
            raise GitHubUnavailableError() from None

    # ---- GitHub App (installation) access -----------------------------------

    def install_url(self, *, state: str) -> str:
        query = urlencode({"state": state})
        return f"{GITHUB_WEB_URL}/apps/{self._app_slug}/installations/new?{query}"

    def _app_jwt(self) -> str:
        """A short-lived token proving we are the App. Never stored or logged."""
        if not self.is_app_configured:
            raise NotConfiguredError()
        try:
            private_key = Path(self._private_key_path).read_text()
            now = int(time.time())
            return jwt.encode(
                {
                    "iat": now - APP_JWT_BACKDATE_SECONDS,
                    "exp": now + APP_JWT_LIFETIME_SECONDS,
                    "iss": self._app_id,
                },
                private_key,
                algorithm="RS256",
            )
        except (OSError, ValueError, jwt.PyJWTError):
            # Never include the exception text: it could mention key material.
            logger.error("could not sign the github app token; check the private key file")
            raise NotConfiguredError() from None

    async def _api_request(
        self,
        method: str,
        path: str,
        *,
        bearer: str,
        json: dict | None = None,
        params: dict | None = None,
        app_level: bool = False,
    ) -> httpx.Response:
        """Call the GitHub API and turn failures into internal errors.

        `app_level` is true for calls authenticated with the app JWT, where a 401
        means our own configuration is wrong rather than that access was revoked.
        """
        try:
            response = await self._http.request(
                method,
                f"{GITHUB_API_URL}{path}",
                json=json,
                params=params,
                headers={
                    "Authorization": f"Bearer {bearer}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        except httpx.HTTPError as exc:
            logger.warning("github api request failed", extra={"error": type(exc).__name__})
            raise GitHubUnavailableError() from None

        status = response.status_code
        if status < 400:
            return response

        message = _error_message(response)
        rate_limited = (
            status == 429
            or response.headers.get("x-ratelimit-remaining") == "0"
            or response.headers.get("retry-after") is not None
            or "rate limit" in message
        )
        if rate_limited and status in (403, 429):
            retry_after, reset_at = _rate_limit_wait(response)
            logger.warning("github rate limit reached", extra={"status": status})
            raise GitHubRateLimitedError(retry_after=retry_after, reset_at=reset_at)
        if status >= 500:
            logger.warning("github api error", extra={"status": status})
            raise GitHubUnavailableError()
        if status == 401:
            if app_level:
                logger.error("github rejected the app token; check app id and private key")
                raise NotConfiguredError()
            raise GitHubAccessError(ACCESS_REVOKED)
        if status == 404:
            raise GitHubAccessError(ACCESS_REVOKED)
        if status == 403:
            if "suspended" in message:
                raise GitHubAccessError(SUSPENDED)
            raise GitHubAccessError(PERMISSION_MISSING)
        if status == 422:
            raise GitHubAccessError(PERMISSION_MISSING)
        logger.warning("github api answered unexpectedly", extra={"status": status})
        raise GitHubUnavailableError()

    async def get_installation(self, installation_id: int) -> GitHubInstallation:
        response = await self._api_request(
            "GET", f"/app/installations/{installation_id}", bearer=self._app_jwt(), app_level=True
        )
        try:
            body = response.json()
            account = body["account"]
            return GitHubInstallation(
                id=body["id"],
                account_id=account["id"],
                account_login=account["login"],
                account_type=account["type"],
                permissions=body.get("permissions") or {},
                suspended=body.get("suspended_at") is not None,
            )
        except (ValueError, KeyError, TypeError, ValidationError):
            logger.warning("github installation response was not usable")
            raise GitHubUnavailableError() from None

    async def create_installation_token(self, installation_id: int) -> str:
        """A one-hour token limited to read-only metadata and pull requests."""
        response = await self._api_request(
            "POST",
            f"/app/installations/{installation_id}/access_tokens",
            bearer=self._app_jwt(),
            json={"permissions": TOKEN_PERMISSIONS},
            app_level=True,
        )
        try:
            token = response.json()["token"]
        except (ValueError, KeyError, TypeError):
            logger.warning("github token response was not usable")
            raise GitHubUnavailableError() from None
        if not isinstance(token, str) or not token:
            raise GitHubUnavailableError()
        return token

    async def list_installation_repositories(
        self, installation_token: str
    ) -> list[GitHubRepositoryInfo]:
        """Every repository the installation can access, across all pages."""
        repositories: list[GitHubRepositoryInfo] = []
        for page in range(1, MAX_REPOSITORY_PAGES + 1):
            response = await self._api_request(
                "GET",
                "/installation/repositories",
                bearer=installation_token,
                params={"per_page": REPOSITORIES_PER_PAGE, "page": page},
            )
            logger.info(
                "github repositories page fetched",
                extra={
                    "page": page,
                    "rate_limit_remaining": response.headers.get("x-ratelimit-remaining"),
                },
            )
            try:
                items = response.json()["repositories"]
                repositories.extend(
                    GitHubRepositoryInfo(
                        id=item["id"],
                        name=item["name"],
                        full_name=item["full_name"],
                        owner_login=item["owner"]["login"],
                        is_private=bool(item["private"]),
                    )
                    for item in items
                )
            except (ValueError, KeyError, TypeError, ValidationError):
                logger.warning("github repositories response was not usable")
                raise GitHubUnavailableError() from None
            if len(items) < REPOSITORIES_PER_PAGE:
                break
        return repositories


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    message = body.get("message") if isinstance(body, dict) else None
    return message.lower() if isinstance(message, str) else ""


def _rate_limit_wait(response: httpx.Response) -> tuple[int | None, datetime | None]:
    """Seconds to wait and the reset moment, from GitHub's rate-limit headers."""
    reset_at: datetime | None = None
    retry_after: int | None = None
    raw_retry_after = response.headers.get("retry-after")
    if raw_retry_after and raw_retry_after.isdigit():
        retry_after = int(raw_retry_after)
    raw_reset = response.headers.get("x-ratelimit-reset")
    if raw_reset and raw_reset.isdigit():
        reset_at = datetime.fromtimestamp(int(raw_reset), UTC)
        if retry_after is None:
            retry_after = max(0, int(reset_at.timestamp() - time.time()))
    return retry_after, reset_at
