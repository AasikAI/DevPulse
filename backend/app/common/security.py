import hashlib
import hmac
import secrets


def new_token() -> str:
    """Random URL-safe credential (256 bits). Only its hash is ever stored."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    # SHA-256 is enough for high-entropy random tokens (no slow hash needed).
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
