from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


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
