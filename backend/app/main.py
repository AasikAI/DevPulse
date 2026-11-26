from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.common.logging import configure_logging
from app.common.middleware import OriginCheckMiddleware, RequestContextMiddleware
from app.config import get_settings
from app.db import get_db
from app.github_integration.client import GitHubClient
from app.github_integration.router import router as github_router
from app.identity.router import router as identity_router

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(timeout=10.0) as http:
        app.state.github_client = GitHubClient(
            client_id=settings.github_app_client_id,
            client_secret=settings.github_app_client_secret.get_secret_value(),
            http=http,
            app_id=settings.github_app_id,
            app_slug=settings.github_app_slug,
            private_key_path=settings.github_app_private_key_path,
        )
        yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# The browser reaches the API through the frontend origin (Vite proxy), so
# there is no cross-origin traffic and no CORS configuration.
# Added first so it runs second: the request context wraps everything.
app.add_middleware(OriginCheckMiddleware, allowed_origin=settings.frontend_origin)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"code": exc.code, "message": exc.message}
    )


app.include_router(identity_router, prefix="/api")
app.include_router(github_router, prefix="/api")


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    body = {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "up",
    }
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        body["status"] = "degraded"
        body["database"] = "down"
        return JSONResponse(status_code=503, content=body)
    return body
