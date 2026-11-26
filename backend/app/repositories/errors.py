from app.common.errors import AppError


class NoConnectionError(AppError):
    code = "not_connected"
    message = "Connect your GitHub account first."
    status_code = 409


class RepositoryNotFoundError(AppError):
    """Also used for repositories that belong to someone else, so IDs cannot be probed."""

    code = "repository_not_found"
    message = "One of the selected repositories was not found."
    status_code = 404


class RepositoryUnavailableError(AppError):
    code = "repository_unavailable"
    message = "DevPulse can no longer access one of the selected repositories on GitHub."
    status_code = 409
