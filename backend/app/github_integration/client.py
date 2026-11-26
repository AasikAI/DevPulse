import logging
from urllib.parse import urlencode

import httpx
from pydantic import ValidationError

from app.github_integration.errors import GitHubAuthorizationError, GitHubUnavailableError
from app.github_integration.schemas import GitHubUser

logger = logging.getLogger(__name__)

GITHUB_WEB_URL = "https://github.com"
GITHUB_API_URL = "https://api.github.com"


class GitHubClient:
    """The only place that talks to GitHub.

    Slice 1 covers the user sign-in flow. The user token returned by
    `exchange_code` is meant to be used once and thrown away, never stored.
    """

    def __init__(
        self, *, client_id: str, client_secret: str, http: httpx.AsyncClient
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http

    @property
    def is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

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
