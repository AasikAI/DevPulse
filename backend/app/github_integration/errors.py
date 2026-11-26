from datetime import datetime

from app.common.errors import AppError


class GitHubUnavailableError(AppError):
    """GitHub is down, rate limiting us, or the network failed. Retryable."""

    code = "github_unavailable"
    message = "GitHub is not responding right now. Please try again in a moment."
    status_code = 502

    def __init__(self, *, retry_after: int | None = None) -> None:
        super().__init__()
        # Seconds GitHub asked us to wait, when it said so.
        self.retry_after = retry_after


class GitHubRateLimitedError(GitHubUnavailableError):
    """GitHub's rate limit is used up. Retry after the reset time."""

    def __init__(self, *, retry_after: int | None, reset_at: datetime | None) -> None:
        super().__init__(retry_after=retry_after)
        self.reset_at = reset_at


class GitHubAuthorizationError(AppError):
    """GitHub rejected the authorization code or token. Not retryable."""

    code = "github_authorization_failed"
    message = "GitHub did not accept the authorization."
    status_code = 401


class GitHubAccessError(AppError):
    """The App installation is gone, suspended, or lacks a permission.

    Not retryable: the user has to fix it on GitHub. `reason` is a fixed code
    that is safe to store and show.
    """

    code = "github_access_problem"
    message = "DevPulse can no longer use your GitHub connection."
    status_code = 409

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason


ACCESS_REVOKED = "access_revoked"
PERMISSION_MISSING = "permission_missing"
SUSPENDED = "suspended"


class InvalidInstallStateError(AppError):
    code = "invalid_state"
    message = "That connection attempt was invalid or has already been used."
    status_code = 400


class InstallationNotAllowedError(AppError):
    code = "installation_not_allowed"
    message = "This GitHub installation cannot be connected to your account."
    status_code = 403


class InstallFailedError(AppError):
    code = "failed"
    message = "Connecting GitHub failed. Please try again."
    status_code = 400
