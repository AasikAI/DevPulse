import uuid
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import httpx
from sqlalchemy import text

from app.db import SessionLocal
from app.github_integration.models import GithubConnection
from app.github_integration.repository import ConnectionRepository
from app.github_integration.schemas import GitHubRepositoryInfo
from app.identity.repository import IdentityRepository
from app.repositories.repository import RepositoryRepository
from tests.fake_github import GOOD_CODE


async def start_sign_in(client: httpx.AsyncClient) -> str:
    """Click 'Continue with GitHub'; returns the state GitHub would echo back."""
    response = await client.get("/api/auth/github/login")
    assert response.status_code == 302
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


async def sign_in(client: httpx.AsyncClient, code: str = GOOD_CODE) -> httpx.Response:
    state = await start_sign_in(client)
    return await client.get("/api/auth/github/callback", params={"code": code, "state": state})


async def scalar(sql: str):
    async with SessionLocal() as session:
        return (await session.execute(text(sql))).scalar_one()


async def start_install(client: httpx.AsyncClient) -> str:
    """Click 'Connect GitHub'; returns the state GitHub would echo back to the setup URL."""
    response = await client.get("/api/github/install")
    assert response.status_code == 302
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


async def finish_install(
    client: httpx.AsyncClient,
    *,
    installation_id: int | str = 5001,
    state: str | None = None,
    setup_action: str = "install",
) -> httpx.Response:
    params: dict[str, str] = {"installation_id": str(installation_id), "setup_action": setup_action}
    if state is not None:
        params["state"] = state
    return await client.get("/api/github/install/callback", params=params)


async def connect(client: httpx.AsyncClient, installation_id: int = 5001) -> httpx.Response:
    """Sign-in must already be done. Runs the whole install round trip."""
    state = await start_install(client)
    return await finish_install(client, installation_id=installation_id, state=state)


async def make_connection(
    *,
    github_user_id: int = 1001,
    installation_id: int = 5001,
    status: str = "active",
    reason: str | None = None,
) -> uuid.UUID:
    """Create a user and connection directly in the database; returns the connection ID."""
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        user = await IdentityRepository(session).upsert_user(
            github_user_id=github_user_id,
            login=f"user-{github_user_id}",
            name=None,
            avatar_url=None,
            email=None,
            now=now,
        )
        connection: GithubConnection = await ConnectionRepository(session).upsert_for_user(
            user_id=user.id,
            installation_id=installation_id,
            github_account_id=github_user_id,
            github_account_login=f"user-{github_user_id}",
            account_type="User",
            permissions={"metadata": "read", "pull_requests": "read"},
            status=status,
            status_reason=reason,
            now=now,
        )
        await session.commit()
        return connection.id


async def store_repositories(connection_id: uuid.UUID, repos: list[GitHubRepositoryInfo]) -> None:
    async with SessionLocal() as session:
        repository = RepositoryRepository(session)
        await repository.upsert_many(
            connection_id=connection_id, repositories=repos, now=datetime.now(UTC)
        )
        await session.commit()
