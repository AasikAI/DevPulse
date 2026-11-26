import os

# Must run before the app is imported: settings and the DB engine are built at import.
# Credentials for PostgreSQL come from the root .env or the environment; only the
# database name is forced to a separate test database.
os.environ["ENVIRONMENT"] = "test"
os.environ["POSTGRES_DB"] = "devpulse_test"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
os.environ["GITHUB_APP_CLIENT_ID"] = "test-client-id"
os.environ["GITHUB_APP_CLIENT_SECRET"] = "test-client-secret"

import asyncio  # noqa: E402
from collections.abc import AsyncIterator, Callable  # noqa: E402
from pathlib import Path  # noqa: E402

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.github_integration.client import GitHubClient  # noqa: E402
from app.github_integration.dependencies import get_github_client  # noqa: E402
from app.main import app  # noqa: E402
from tests.fake_github import FakeGitHub  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
ORIGIN = "http://localhost:5173"


async def _ensure_test_database() -> None:
    settings = get_settings()
    assert settings.postgres_db.endswith("_test"), "refusing to wipe a non-test database"
    connection = await asyncpg.connect(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database="postgres",
    )
    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.postgres_db
        )
        if not exists:
            await connection.execute(f'CREATE DATABASE "{settings.postgres_db}"')
    finally:
        await connection.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    """A fresh schema built by the real Alembic migrations, once per test run."""
    await _ensure_test_database()
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))

    # No ini file on purpose: env.py would otherwise reconfigure logging.
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    # Alembic's env.py starts its own event loop, so run it off this loop's thread.
    await asyncio.to_thread(command.upgrade, config, "head")
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(database: None) -> None:
    async with SessionLocal() as session:
        await session.execute(text("TRUNCATE users, sessions, oauth_states CASCADE"))
        await session.commit()


@pytest.fixture
def github() -> FakeGitHub:
    return FakeGitHub()


@pytest_asyncio.fixture
async def new_browser(github: FakeGitHub) -> AsyncIterator[Callable[[], httpx.AsyncClient]]:
    """Each call gives a client with its own cookie jar, like a separate browser."""
    fake_http = httpx.AsyncClient(transport=httpx.MockTransport(github.handler))
    github_client = GitHubClient(
        client_id="test-client-id", client_secret="test-client-secret", http=fake_http
    )
    app.dependency_overrides[get_github_client] = lambda: github_client
    created: list[httpx.AsyncClient] = []

    def make() -> httpx.AsyncClient:
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=ORIGIN, headers={"Origin": ORIGIN}
        )
        created.append(client)
        return client

    yield make
    for client in created:
        await client.aclose()
    await fake_http.aclose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def browser(new_browser: Callable[[], httpx.AsyncClient]) -> httpx.AsyncClient:
    return new_browser()
