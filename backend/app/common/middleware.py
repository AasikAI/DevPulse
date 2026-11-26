import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.common.errors import OriginNotAllowedError
from app.common.logging import request_id_var

logger = logging.getLogger("app.request")

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID and logs one line per request.

    The query string is deliberately not logged: OAuth callbacks carry a
    one-time code and state there.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid.uuid4().hex
        request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request failed",
                extra={"method": request.method, "path": request.url.path},
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return response


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """CSRF defence for state-changing requests.

    The session cookie is SameSite=Lax; on top of that every unsafe request
    must come from the DevPulse frontend origin.
    """

    def __init__(self, app, allowed_origin: str) -> None:
        super().__init__(app)
        self._allowed_origin = allowed_origin

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _SAFE_METHODS:
            if request.headers.get("origin") != self._allowed_origin:
                error = OriginNotAllowedError()
                return JSONResponse(
                    status_code=error.status_code,
                    content={"code": error.code, "message": error.message},
                )
        return await call_next(request)
