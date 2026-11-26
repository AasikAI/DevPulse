from app.common.errors import AppError


class GitHubUnavailableError(AppError):
    """GitHub is down, rate limiting us, or the network failed. Retryable."""

    code = "github_unavailable"
    message = "GitHub is not responding right now. Please try again in a moment."
    status_code = 502


class GitHubAuthorizationError(AppError):
    """GitHub rejected the authorization code or token. Not retryable."""

    code = "github_authorization_failed"
    message = "GitHub did not accept the authorization."
    status_code = 401
