import json
import logging

from app.common.logging import JsonFormatter, redact_text


def format_record(message: str, **extra) -> dict:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, (), None)
    for key, value in extra.items():
        setattr(record, key, value)
    return json.loads(JsonFormatter().format(record))


def test_github_tokens_and_bearer_headers_are_redacted():
    text = "calling with ghu_abcdefghijklmnopqrstuvwxyz0123 and Bearer abc.def-123456"

    redacted = redact_text(text)

    assert "ghu_abcdefghijklmnopqrstuvwxyz0123" not in redacted
    assert "abc.def-123456" not in redacted


def test_credentials_in_query_strings_and_cookies_are_redacted():
    redacted = redact_text("GET /cb?code=abc123&state=xyz789 cookie devpulse_session=rawvalue")

    assert "abc123" not in redacted
    assert "xyz789" not in redacted
    assert "rawvalue" not in redacted


def test_sensitive_extra_fields_are_redacted_by_name():
    entry = format_record("event", authorization="Bearer secret-value", cookie="devpulse_session=x", status=200)

    assert entry["authorization"] == "[REDACTED]"
    assert entry["cookie"] == "[REDACTED]"
    assert entry["status"] == 200


def test_exception_text_is_redacted_too():
    try:
        raise RuntimeError("failed with ghp_" + "a" * 30)
    except RuntimeError:
        import sys

        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "boom", (), sys.exc_info())

    assert "ghp_" + "a" * 30 not in JsonFormatter().format(record)
