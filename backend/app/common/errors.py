class AppError(Exception):
    """Base for application errors.

    `code` and `message` are fixed per class so a response can never carry
    internal details (stack traces, GitHub payloads, secrets).
    """

    code = "internal_error"
    message = "Something went wrong. Please try again."
    status_code = 500


class NotAuthenticatedError(AppError):
    code = "not_authenticated"
    message = "You are not signed in."
    status_code = 401


class OriginNotAllowedError(AppError):
    code = "origin_not_allowed"
    message = "This request was not allowed."
    status_code = 403


class NotConfiguredError(AppError):
    code = "not_configured"
    message = "This feature is not available right now."
    status_code = 503
