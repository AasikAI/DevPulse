from app.common.errors import AppError


class SignInError(AppError):
    """Base for sign-in failures that are shown to the user as a short code."""

    code = "failed"
    message = "Sign-in failed. Please try again."
    status_code = 400


class SignInCancelledError(SignInError):
    code = "cancelled"
    message = "Sign-in was cancelled."


class InvalidSignInStateError(SignInError):
    code = "invalid_state"
    message = "That sign-in attempt was invalid or has already been used."
