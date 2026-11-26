import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.identity.models import User, UserSession
from app.identity.repository import IdentityRepository


async def upsert(github_user_id: int, login: str):
    async with SessionLocal() as session:
        repository = IdentityRepository(session)
        user = await repository.upsert_user(
            github_user_id=github_user_id,
            login=login,
            name=None,
            avatar_url=None,
            email=None,
            now=datetime.now(UTC),
        )
        await repository.commit()
        return user


async def test_the_database_rejects_a_second_user_with_the_same_github_id():
    async with SessionLocal() as session:
        for login in ("first", "second"):
            now = datetime.now(UTC)
            session.add(
                User(github_user_id=5, login=login, updated_at=now, last_login_at=now)
            )
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_concurrent_duplicate_callbacks_create_one_user():
    results = await asyncio.gather(*(upsert(42, f"login-{i}") for i in range(5)))

    assert len({user.id for user in results}) == 1
    async with SessionLocal() as session:
        users = (await session.execute(User.__table__.select())).all()
    assert len(users) == 1


async def test_two_concurrent_callbacks_with_the_same_state_only_succeed_once():
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        repository = IdentityRepository(session)
        await repository.create_oauth_state(
            state_hash="s" * 64, nonce_hash="n" * 64, purpose="sign_in", expires_at=now + timedelta(minutes=5)
        )
        await repository.commit()

    async def consume():
        async with SessionLocal() as session:
            repository = IdentityRepository(session)
            result = await repository.consume_oauth_state(
                state_hash="s" * 64, purpose="sign_in", now=now
            )
            await repository.commit()
            return result

    results = await asyncio.gather(consume(), consume())

    assert sorted(r is None for r in results) == [False, True]


async def test_a_state_issued_for_another_purpose_cannot_be_consumed_as_sign_in():
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        repository = IdentityRepository(session)
        await repository.create_oauth_state(
            state_hash="p" * 64, nonce_hash="n" * 64, purpose="install", expires_at=now + timedelta(minutes=5)
        )
        assert await repository.consume_oauth_state(state_hash="p" * 64, purpose="sign_in", now=now) is None


async def test_the_database_rejects_a_duplicate_session_hash():
    user = await upsert(7, "someone")
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        for _ in range(2):
            session.add(
                UserSession(
                    user_id=user.id, token_hash="h" * 64, created_at=now, expires_at=now + timedelta(days=1)
                )
            )
        with pytest.raises(IntegrityError):
            await session.commit()
