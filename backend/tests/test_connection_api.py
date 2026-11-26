import logging
from collections.abc import Callable

import httpx
from sqlalchemy import text

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.github_integration.client import GitHubClient
from app.github_integration.dependencies import get_github_client
from app.main import app
from tests.conftest import ORIGIN, RecordingDispatcher
from tests.fake_github import FAKE_USER_TOKEN, FakeGitHub, make_installation
from tests.helpers import (
    connect,
    finish_install,
    make_connection,
    scalar,
    sign_in,
    start_install,
)

Browser = Callable[[], httpx.AsyncClient]


def connect_url(error: str | None = None) -> str:
    return f"{ORIGIN}/connect" + (f"?error={error}" if error else "")


REPOSITORIES_URL = f"{ORIGIN}/repositories"


# --- Connection status ---------------------------------------------------------------


async def test_status_requires_a_signed_in_user(browser):
    response = await browser.get("/api/github/connection")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


async def test_a_signed_in_user_without_a_connection_is_not_connected(browser):
    await sign_in(browser)

    response = await browser.get("/api/github/connection")

    assert response.status_code == 200
    assert response.json()["status"] == "not_connected"
    assert response.json()["repository_count"] == 0


# --- Scenario: I connect my GitHub account ------------------------------------------


async def test_starting_the_install_sends_me_to_the_github_app_page_with_a_state(browser):
    await sign_in(browser)

    response = await browser.get("/api/github/install")

    assert response.status_code == 302
    assert response.headers["location"].startswith(
        "https://github.com/apps/devpulse-test/installations/new?state="
    )
    cookie = next(c for c in response.headers.get_list("set-cookie") if c.startswith("devpulse_install="))
    assert "httponly" in cookie.lower() and "samesite=lax" in cookie.lower()
    assert "path=/api/github" in cookie.lower()


async def test_starting_the_install_while_signed_out_goes_to_sign_in(browser):
    response = await browser.get("/api/github/install")

    assert response.headers["location"] == f"{ORIGIN}/sign-in"


async def test_installing_the_app_connects_my_account_and_fetches_my_repositories(
    browser, dispatcher: RecordingDispatcher
):
    await sign_in(browser)

    callback = await connect(browser)

    assert callback.headers["location"] == REPOSITORIES_URL
    status = (await browser.get("/api/github/connection")).json()
    assert status["status"] == "active"
    assert status["account_login"] == "octocat"
    assert status["repositories_synced_at"] is None  # the job has not run yet
    connection_id = await scalar("SELECT id FROM github_connections")
    owner = await scalar("SELECT u.github_user_id FROM github_connections c JOIN users u ON u.id = c.user_id")
    assert owner == 1001
    # Exactly one job is queued, with the internal connection ID and nothing else.
    assert dispatcher.calls == [(connection_id, "connected")]


async def test_the_status_response_has_no_installation_id_or_credentials(browser):
    await sign_in(browser)
    await connect(browser)

    body = (await browser.get("/api/github/connection")).json()

    assert set(body) == {
        "status",
        "reason",
        "account_login",
        "connected_at",
        "last_checked_at",
        "repositories_synced_at",
        "repository_count",
    }


async def test_a_duplicate_callback_does_not_create_a_second_connection(browser):
    await sign_in(browser)

    await connect(browser)
    await connect(browser)

    assert await scalar("SELECT count(*) FROM github_connections") == 1


async def test_reinstalling_under_a_new_installation_id_updates_the_same_connection(
    browser, github: FakeGitHub
):
    await sign_in(browser)
    await connect(browser)
    first_id = await scalar("SELECT id FROM github_connections")
    github.installations[5002] = make_installation(installation_id=5002)

    await connect(browser, installation_id=5002)

    assert await scalar("SELECT count(*) FROM github_connections") == 1
    assert await scalar("SELECT id FROM github_connections") == first_id
    assert await scalar("SELECT installation_id FROM github_connections") == 5002


async def test_if_the_job_cannot_be_queued_the_connection_is_still_saved(
    browser, dispatcher: RecordingDispatcher
):
    await sign_in(browser)
    dispatcher.can_queue = False

    callback = await connect(browser)

    assert callback.headers["location"] == REPOSITORIES_URL
    assert (await browser.get("/api/github/connection")).json()["status"] == "active"


# --- Install callback safety -----------------------------------------------------------


async def test_the_install_callback_while_signed_out_creates_nothing(browser):
    response = await finish_install(browser, state="whatever")

    assert response.headers["location"] == f"{ORIGIN}/sign-in"
    assert await scalar("SELECT count(*) FROM github_connections") == 0


async def test_a_reused_install_state_is_rejected(browser, dispatcher: RecordingDispatcher):
    await sign_in(browser)
    state = await start_install(browser)
    nonce = browser.cookies["devpulse_install"]
    await finish_install(browser, state=state)
    browser.cookies.set("devpulse_install", nonce, path="/api/github")

    replay = await finish_install(browser, state=state)

    assert replay.headers["location"] == connect_url("invalid_state")
    assert len(dispatcher.calls) == 1


async def test_a_forged_install_state_is_rejected(browser):
    await sign_in(browser)
    await start_install(browser)

    response = await finish_install(browser, state="forged")

    assert response.headers["location"] == connect_url("invalid_state")
    assert await scalar("SELECT count(*) FROM github_connections") == 0


async def test_an_install_state_from_another_browser_is_rejected(new_browser: Browser):
    victim, attacker = new_browser(), new_browser()
    await sign_in(victim)
    await sign_in(attacker)
    state = await start_install(attacker)

    response = await finish_install(victim, state=state)  # no nonce cookie in the victim's browser

    assert response.headers["location"] == connect_url("invalid_state")
    assert await scalar("SELECT count(*) FROM github_connections") == 0


async def test_an_install_state_cannot_be_used_by_a_different_user(
    new_browser: Browser, github: FakeGitHub
):
    first, second = new_browser(), new_browser()
    await sign_in(first)
    github.user = {**github.user, "id": 2002, "login": "other"}
    await sign_in(second)
    github.installations[6002] = make_installation(6002, account_id=2002, login="other")
    state = await start_install(first)
    second.cookies.set("devpulse_install", first.cookies["devpulse_install"], path="/api/github")

    response = await finish_install(second, installation_id=6002, state=state)

    assert response.headers["location"] == connect_url("invalid_state")
    assert await scalar("SELECT count(*) FROM github_connections") == 0


async def test_an_installation_on_someone_elses_account_is_rejected(
    browser, github: FakeGitHub, dispatcher: RecordingDispatcher
):
    github.installations[7001] = make_installation(7001, account_id=9999, login="stranger")
    await sign_in(browser)

    response = await connect(browser, installation_id=7001)

    assert response.headers["location"] == connect_url("installation_not_allowed")
    assert await scalar("SELECT count(*) FROM github_connections") == 0
    assert dispatcher.calls == []


async def test_an_organisation_installation_is_rejected(browser, github: FakeGitHub):
    github.installations[7002] = make_installation(7002, account_type="Organization")
    await sign_in(browser)

    response = await connect(browser, installation_id=7002)

    assert response.headers["location"] == connect_url("installation_not_allowed")
    assert await scalar("SELECT count(*) FROM github_connections") == 0


async def test_an_installation_that_does_not_exist_on_github_is_rejected(browser):
    await sign_in(browser)

    response = await connect(browser, installation_id=424242)

    assert response.headers["location"] == connect_url("installation_not_allowed")


async def test_a_missing_or_malformed_installation_id_fails_safely(browser):
    await sign_in(browser)
    state = await start_install(browser)

    response = await finish_install(browser, installation_id="not-a-number", state=state)

    assert response.headers["location"] == connect_url("failed")


async def test_github_being_down_during_the_callback_shows_a_retryable_message(
    browser, github: FakeGitHub, caplog
):
    caplog.set_level(logging.INFO)
    await sign_in(browser)
    state = await start_install(browser)
    github.installation_error = (503, {}, {"message": "unavailable"})

    response = await finish_install(browser, state=state)

    assert response.headers["location"] == connect_url("github_unavailable")
    # The cause is traceable in the server log even though the browser only sees a code.
    assert any(
        r.getMessage() == "install callback rejected" and r.__dict__["code"] == "github_unavailable"
        for r in caplog.records
    )


async def test_install_is_unavailable_until_the_github_app_is_configured(browser):
    await sign_in(browser)
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        client_id="x", client_secret="y", http=httpx.AsyncClient()
    )

    response = await browser.get("/api/github/install")

    assert response.headers["location"] == connect_url("not_configured")


# --- "Redirect on update" (GitHub sends no state when repositories change) ------------


async def test_updating_repository_access_on_github_refreshes_my_repositories(
    browser, dispatcher: RecordingDispatcher
):
    await sign_in(browser)
    await connect(browser)
    dispatcher.calls.clear()

    response = await finish_install(browser, setup_action="update")

    assert response.headers["location"] == REPOSITORIES_URL
    assert len(dispatcher.calls) == 1


async def test_an_update_callback_without_state_cannot_create_a_connection(browser):
    await sign_in(browser)

    response = await finish_install(browser, setup_action="update")

    assert response.headers["location"] == connect_url("invalid_state")
    assert await scalar("SELECT count(*) FROM github_connections") == 0


# --- Access problems found at install time --------------------------------------------


async def test_a_suspended_installation_needs_attention_and_is_not_fetched(
    browser, github: FakeGitHub, dispatcher: RecordingDispatcher
):
    github.installations[5001] = make_installation(suspended=True)
    await sign_in(browser)

    await connect(browser)

    status = (await browser.get("/api/github/connection")).json()
    assert (status["status"], status["reason"]) == ("needs_attention", "suspended")
    assert dispatcher.calls == []


async def test_a_connection_that_needs_attention_stays_on_the_connect_page(
    browser, github: FakeGitHub
):
    github.installations[5001] = make_installation(suspended=True)
    await sign_in(browser)

    response = await connect(browser)

    assert response.headers["location"] == connect_url()


async def test_a_missing_pull_request_permission_needs_attention(
    browser, github: FakeGitHub, dispatcher: RecordingDispatcher
):
    github.installations[5001] = make_installation(permissions={"metadata": "read"})
    await sign_in(browser)

    await connect(browser)

    status = (await browser.get("/api/github/connection")).json()
    assert (status["status"], status["reason"]) == ("needs_attention", "permission_missing")
    assert dispatcher.calls == []


# --- Scenario: I only see my own data --------------------------------------------------


async def test_another_users_connection_is_never_visible_to_me(
    new_browser: Browser, github: FakeGitHub
):
    mine, theirs = new_browser(), new_browser()
    await sign_in(mine)
    await connect(mine)
    github.user = {**github.user, "id": 2002, "login": "other"}
    await sign_in(theirs)

    status = (await theirs.get("/api/github/connection")).json()

    assert status == {
        "status": "not_connected",
        "reason": None,
        "account_login": None,
        "connected_at": None,
        "last_checked_at": None,
        "repositories_synced_at": None,
        "repository_count": 0,
    }


async def test_the_status_counts_only_my_available_repositories(browser):
    from app.github_integration.schemas import GitHubRepositoryInfo
    from tests.helpers import store_repositories

    await sign_in(browser)
    await connect(browser)
    connection_id = await scalar("SELECT id FROM github_connections")
    other_connection = await make_connection(github_user_id=2002, installation_id=6002)
    repos = [GitHubRepositoryInfo(id=i, name=f"r{i}", full_name=f"o/r{i}", owner_login="o", is_private=False) for i in (1, 2, 3)]
    await store_repositories(connection_id, repos)
    await store_repositories(other_connection, repos)
    async with SessionLocal() as session:
        await session.execute(text("UPDATE repositories SET is_available = false WHERE github_repo_id = 3"))
        await session.commit()

    status = (await browser.get("/api/github/connection")).json()

    assert status["repository_count"] == 2


# --- Security assertions ----------------------------------------------------------------


async def test_no_secret_appears_in_logs_during_the_install(browser, caplog):
    caplog.set_level(logging.DEBUG)
    await sign_in(browser)
    state = await start_install(browser)
    nonce = browser.cookies["devpulse_install"]

    await finish_install(browser, state=state)

    logged = " ".join(
        f"{record.getMessage()} {sorted(map(str, record.__dict__.values()))}" for record in caplog.records
    )
    for secret in (FAKE_USER_TOKEN, "test-client-secret", state, nonce, "BEGIN"):
        assert secret not in logged
