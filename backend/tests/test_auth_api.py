import logging
from collections.abc import Callable
from urllib.parse import parse_qs, urlparse

import httpx
from sqlalchemy import text

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.github_integration.client import GitHubClient
from app.github_integration.dependencies import get_github_client
from app.main import app
from tests.conftest import ORIGIN
from tests.fake_github import FAKE_USER_TOKEN, GOOD_CODE, FakeGitHub

Browser = Callable[[], httpx.AsyncClient]


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


# --- Scenario: A new user signs in with GitHub -----------------------------


async def test_new_user_signs_in_and_is_sent_to_the_start_page(browser, github):
    callback = await sign_in(browser)

    assert callback.status_code == 302
    assert callback.headers["location"] == f"{ORIGIN}/start"
    assert await scalar("SELECT count(*) FROM users WHERE github_user_id = 1001") == 1
    me = await browser.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["login"] == "octocat"


async def test_signed_in_session_survives_a_refresh(browser):
    await sign_in(browser)

    first = await browser.get("/api/auth/me")
    second = await browser.get("/api/auth/me")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


async def test_me_response_has_no_credentials_or_github_ids(browser):
    await sign_in(browser)

    body = (await browser.get("/api/auth/me")).json()

    assert set(body) == {"id", "login", "name", "avatar_url", "email"}


async def test_user_without_a_public_email_can_sign_in(browser, github: FakeGitHub):
    github.user["email"] = None

    await sign_in(browser)

    assert (await browser.get("/api/auth/me")).json()["email"] is None


# --- Scenario: A returning user signs in again -----------------------------


async def test_returning_user_is_the_same_user_and_no_second_user_is_created(
    new_browser: Browser, github: FakeGitHub
):
    first = new_browser()
    await sign_in(first)
    first_id = (await first.get("/api/auth/me")).json()["id"]

    github.user["login"] = "octocat-renamed"
    second = new_browser()
    await sign_in(second)
    me = (await second.get("/api/auth/me")).json()

    assert me["id"] == first_id
    assert me["login"] == "octocat-renamed"
    assert await scalar("SELECT count(*) FROM users") == 1


async def test_signing_in_again_replaces_this_browsers_old_session(browser):
    await sign_in(browser)
    old_cookie = browser.cookies["devpulse_session"]

    await sign_in(browser)

    assert browser.cookies["devpulse_session"] != old_cookie
    assert await scalar("SELECT count(*) FROM sessions") == 2
    assert await scalar("SELECT count(*) FROM sessions WHERE revoked_at IS NOT NULL") == 1
    assert (await browser.get("/api/auth/me")).status_code == 200


# --- Scenario: Sign-in is cancelled or fails -------------------------------


async def test_cancelling_on_github_leaves_me_signed_out_with_a_safe_message(browser):
    await start_sign_in(browser)

    response = await browser.get(
        "/api/auth/github/callback", params={"error": "access_denied", "state": "x"}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=cancelled"
    assert (await browser.get("/api/auth/me")).status_code == 401


async def test_callback_with_an_unknown_state_is_rejected(browser):
    await start_sign_in(browser)

    response = await browser.get(
        "/api/auth/github/callback", params={"code": GOOD_CODE, "state": "forged"}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=invalid_state"
    assert await scalar("SELECT count(*) FROM users") == 0


async def test_callback_without_code_or_state_is_rejected(browser):
    response = await browser.get("/api/auth/github/callback")

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=invalid_state"


async def test_a_state_can_only_be_used_once(browser):
    state = await start_sign_in(browser)
    nonce = browser.cookies["devpulse_oauth"]
    params = {"code": GOOD_CODE, "state": state}
    first = await browser.get("/api/auth/github/callback", params=params)
    # Replay with the correct nonce, so only the single-use state can stop it.
    browser.cookies.set("devpulse_oauth", nonce, path="/api/auth")

    replay = await browser.get("/api/auth/github/callback", params=params)

    assert first.headers["location"] == f"{ORIGIN}/start"
    assert replay.headers["location"] == f"{ORIGIN}/sign-in?error=invalid_state"
    assert await scalar("SELECT count(*) FROM users") == 1


async def test_callback_from_another_browser_is_rejected(new_browser: Browser):
    victim = new_browser()
    attacker = new_browser()
    state = await start_sign_in(attacker)

    # The victim's browser (no nonce cookie from the attacker's login) follows the link.
    response = await victim.get(
        "/api/auth/github/callback", params={"code": GOOD_CODE, "state": state}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=invalid_state"
    assert (await victim.get("/api/auth/me")).status_code == 401
    assert await scalar("SELECT count(*) FROM users") == 0


async def test_an_expired_state_is_rejected(browser):
    state = await start_sign_in(browser)
    async with SessionLocal() as session:
        await session.execute(text("UPDATE oauth_states SET expires_at = now() - interval '1 minute'"))
        await session.commit()

    response = await browser.get(
        "/api/auth/github/callback", params={"code": GOOD_CODE, "state": state}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=invalid_state"


async def test_a_code_github_rejects_fails_safely_and_burns_the_state(browser):
    state = await start_sign_in(browser)

    response = await browser.get(
        "/api/auth/github/callback", params={"code": "reused-code", "state": state}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=failed"
    assert await scalar("SELECT count(*) FROM oauth_states WHERE consumed_at IS NOT NULL") == 1
    assert await scalar("SELECT count(*) FROM users") == 0


async def test_github_being_down_during_sign_in_shows_a_retryable_message(browser, github):
    state = await start_sign_in(browser)
    github.unavailable = True

    response = await browser.get(
        "/api/auth/github/callback", params={"code": GOOD_CODE, "state": state}
    )

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=github_unavailable"


async def test_sign_in_is_unavailable_until_the_github_app_is_configured(browser):
    unconfigured = Settings(github_app_client_id="", github_app_client_secret="")
    app.dependency_overrides[get_settings] = lambda: unconfigured
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        client_id="", client_secret="", http=httpx.AsyncClient()
    )
    try:
        response = await browser.get("/api/auth/github/login")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.headers["location"] == f"{ORIGIN}/sign-in?error=not_configured"


# --- Sessions and cookies ----------------------------------------------------


async def test_unauthenticated_me_is_a_safe_401(browser):
    response = await browser.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"code": "not_authenticated", "message": "You are not signed in."}


async def test_session_cookie_is_http_only_lax_and_scoped_to_the_whole_site(browser):
    callback = await sign_in(browser)

    cookie = next(
        value for value in callback.headers.get_list("set-cookie") if value.startswith("devpulse_session=")
    ).lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age=1209600" in cookie  # 14 days
    assert "secure" not in cookie  # local development runs on plain http


async def test_session_cookie_is_secure_in_production(browser):
    production = Settings(environment="production")
    app.dependency_overrides[get_settings] = lambda: production
    try:
        callback = await sign_in(browser)
    finally:
        app.dependency_overrides.pop(get_settings, None)

    cookies = [c.lower() for c in callback.headers.get_list("set-cookie")]
    assert all("secure" in c for c in cookies if c.startswith("devpulse_session="))


async def test_only_a_hash_of_the_session_credential_is_stored(browser):
    await sign_in(browser)
    raw = browser.cookies["devpulse_session"]

    async with SessionLocal() as session:
        stored = (await session.execute(text("SELECT token_hash FROM sessions"))).scalar_one()
        dump = (await session.execute(text("SELECT row_to_json(s)::text FROM sessions s"))).scalar_one()

    assert stored != raw
    assert raw not in dump


async def test_an_expired_session_is_rejected(browser):
    await sign_in(browser)
    async with SessionLocal() as session:
        await session.execute(text("UPDATE sessions SET expires_at = now() - interval '1 second'"))
        await session.commit()

    assert (await browser.get("/api/auth/me")).status_code == 401


async def test_the_github_user_token_is_never_stored(browser):
    await sign_in(browser)

    async with SessionLocal() as session:
        dump = (
            await session.execute(
                text(
                    "SELECT (SELECT string_agg(row_to_json(u)::text, '') FROM users u)"
                    " || (SELECT coalesce(string_agg(row_to_json(s)::text, ''), '') FROM sessions s)"
                    " || (SELECT coalesce(string_agg(row_to_json(o)::text, ''), '') FROM oauth_states o)"
                )
            )
        ).scalar_one()

    assert FAKE_USER_TOKEN not in dump
    assert "test-client-secret" not in dump


# --- Scenario: I log out -----------------------------------------------------


async def test_logging_out_ends_only_this_browsers_session(new_browser: Browser):
    laptop, phone = new_browser(), new_browser()
    await sign_in(laptop)
    await sign_in(phone)
    users_before = await scalar("SELECT count(*) FROM users")

    response = await laptop.post("/api/auth/logout")

    assert response.status_code == 204
    assert (await laptop.get("/api/auth/me")).status_code == 401
    assert (await phone.get("/api/auth/me")).status_code == 200
    assert await scalar("SELECT count(*) FROM users") == users_before == 1
    assert await scalar("SELECT count(*) FROM sessions WHERE revoked_at IS NOT NULL") == 1


async def test_logging_out_twice_is_harmless(browser):
    await sign_in(browser)

    assert (await browser.post("/api/auth/logout")).status_code == 204
    assert (await browser.post("/api/auth/logout")).status_code == 204


async def test_a_revoked_session_cannot_be_reused(browser):
    await sign_in(browser)
    stolen = browser.cookies["devpulse_session"]
    await browser.post("/api/auth/logout")

    browser.cookies.set("devpulse_session", stolen, path="/")

    assert (await browser.get("/api/auth/me")).status_code == 401


# --- CSRF: state-changing requests must come from the frontend origin ---------


async def test_logout_from_another_origin_is_rejected_and_keeps_the_session(browser):
    await sign_in(browser)

    evil = await browser.post("/api/auth/logout", headers={"Origin": "https://evil.example"})
    missing = await browser.post("/api/auth/logout", headers={"Origin": ""})

    assert evil.status_code == missing.status_code == 403
    assert evil.json()["code"] == "origin_not_allowed"
    assert (await browser.get("/api/auth/me")).status_code == 200


# --- No secrets in logs ------------------------------------------------------


async def test_no_secret_appears_in_logs_during_sign_in(browser, caplog):
    caplog.set_level(logging.DEBUG)

    state = await start_sign_in(browser)
    nonce = browser.cookies["devpulse_oauth"]
    callback = await browser.get(
        "/api/auth/github/callback", params={"code": GOOD_CODE, "state": state}
    )
    session_cookie = browser.cookies["devpulse_session"]

    logged = " ".join(
        f"{record.getMessage()} {sorted(map(str, record.__dict__.values()))}" for record in caplog.records
    )
    assert callback.status_code == 302
    for secret in (FAKE_USER_TOKEN, "test-client-secret", GOOD_CODE, state, nonce, session_cookie):
        assert secret not in logged
