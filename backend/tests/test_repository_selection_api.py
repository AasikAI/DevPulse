import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from sqlalchemy import text

from app.db import SessionLocal
from app.github_integration.schemas import GitHubRepositoryInfo
from app.repositories.repository import RepositoryRepository
from tests.conftest import ORIGIN
from tests.fake_github import FakeGitHub, make_installation
from tests.helpers import connect, scalar, sign_in, store_repositories

Browser = Callable[[], httpx.AsyncClient]


def repo(repo_id: int, name: str | None = None) -> GitHubRepositoryInfo:
    name = name or f"repo-{repo_id}"
    return GitHubRepositoryInfo(
        id=repo_id, name=name, full_name=f"octocat/{name}", owner_login="octocat", is_private=False
    )


async def connected_with_repositories(
    browser: httpx.AsyncClient, repos: list[GitHubRepositoryInfo] | None = None, fetched: bool = True
) -> uuid.UUID:
    """Signed in, connected, and the background job has stored the repositories."""
    await sign_in(browser)
    await connect(browser)
    connection_id = await scalar("SELECT id FROM github_connections")
    await store_repositories(connection_id, repos if repos is not None else [repo(1), repo(2), repo(3)])
    if fetched:
        async with SessionLocal() as session:
            await session.execute(text("UPDATE github_connections SET repositories_synced_at = now()"))
            await session.commit()
    return connection_id


async def listing(browser: httpx.AsyncClient, **params) -> dict:
    response = await browser.get("/api/repositories", params=params)
    assert response.status_code == 200, response.text
    return response.json()


async def ids_by_name(browser: httpx.AsyncClient) -> dict[str, str]:
    return {item["full_name"].split("/")[1]: item["id"] for item in (await listing(browser))["items"]}


# --- Listing ------------------------------------------------------------------------------


async def test_the_list_requires_a_signed_in_user(browser):
    response = await browser.get("/api/repositories")

    assert response.status_code == 401


async def test_the_list_needs_a_connection(browser):
    await sign_in(browser)

    response = await browser.get("/api/repositories")

    assert response.status_code == 409
    assert response.json()["code"] == "not_connected"


async def test_the_list_says_when_repositories_are_still_being_fetched(browser):
    await connected_with_repositories(browser, repos=[], fetched=False)

    body = await listing(browser)

    assert body["list_status"] == "syncing"
    assert body["refreshed_at"] is None
    assert body["items"] == []


async def test_connected_user_sees_the_repositories_the_app_can_access_by_name(browser):
    await connected_with_repositories(browser, [repo(1, "zeta"), repo(2, "Alpha"), repo(3, "beta")])

    body = await listing(browser)

    assert body["list_status"] == "ready"
    assert body["refreshed_at"] is not None
    assert [i["full_name"] for i in body["items"]] == ["octocat/Alpha", "octocat/beta", "octocat/zeta"]
    assert (body["total"], body["selected_count"]) == (3, 0)
    assert all(i["is_selected"] is False for i in body["items"])


async def test_list_items_carry_no_github_ids_or_connection_details(browser):
    await connected_with_repositories(browser)

    (first, *_) = (await listing(browser))["items"]

    assert set(first) == {"id", "full_name", "is_private", "is_selected"}


async def test_the_list_is_paginated(browser):
    await connected_with_repositories(browser, [repo(i, f"repo-{i}") for i in range(1, 6)])

    page_3 = await listing(browser, page=3, page_size=2)

    assert page_3["total"] == 5
    assert [i["full_name"] for i in page_3["items"]] == ["octocat/repo-5"]
    assert (page_3["page"], page_3["page_size"]) == (3, 2)
    assert (await listing(browser, page=4, page_size=2))["items"] == []


async def test_the_page_size_is_bounded(browser):
    await connected_with_repositories(browser)

    assert (await browser.get("/api/repositories", params={"page_size": 101})).status_code == 422
    assert (await browser.get("/api/repositories", params={"page_size": 0})).status_code == 422
    assert (await browser.get("/api/repositories", params={"page": 0})).status_code == 422


async def test_search_finds_repositories_by_name_ignoring_case(browser):
    await connected_with_repositories(browser, [repo(1, "Platform-API"), repo(2, "web-console"), repo(3, "data")])

    body = await listing(browser, q="PLATFORM")

    assert [i["full_name"] for i in body["items"]] == ["octocat/Platform-API"]
    assert body["total"] == 1


async def test_search_treats_wildcard_characters_literally(browser):
    await connected_with_repositories(browser, [repo(1, "alpha"), repo(2, "beta"), repo(3, "my_repo")])

    assert (await listing(browser, q="%"))["total"] == 0
    assert (await listing(browser, q="_"))["total"] == 1  # only "my_repo"


async def test_the_selected_count_ignores_the_search_and_the_page(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"], ids["repo-2"]]})

    body = await listing(browser, q="repo-3", page_size=1)

    assert (body["total"], body["selected_count"]) == (1, 2)


async def test_repositories_the_app_can_no_longer_see_are_not_listed(browser):
    await connected_with_repositories(browser)
    async with SessionLocal() as session:
        await session.execute(text("UPDATE repositories SET is_available = false WHERE github_repo_id = 3"))
        await session.commit()

    body = await listing(browser)

    assert body["total"] == 2
    assert "octocat/repo-3" not in [i["full_name"] for i in body["items"]]


# --- Scenario: I choose which repositories to track ----------------------------------------------


async def test_selecting_repositories_saves_them(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)

    response = await browser.post(
        "/api/repositories/selection", json={"select": [ids["repo-1"], ids["repo-3"]]}
    )

    assert response.status_code == 200
    assert response.json() == {"selected_count": 2}
    body = await listing(browser)
    assert {i["full_name"]: i["is_selected"] for i in body["items"]} == {
        "octocat/repo-1": True,
        "octocat/repo-2": False,
        "octocat/repo-3": True,
    }
    assert body["selected_count"] == 2
    assert await scalar("SELECT count(*) FROM repositories WHERE is_selected AND selected_at IS NOT NULL") == 2


async def test_selecting_and_unselecting_can_be_done_in_one_save(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})

    response = await browser.post(
        "/api/repositories/selection", json={"select": [ids["repo-2"]], "unselect": [ids["repo-1"]]}
    )

    assert response.json() == {"selected_count": 1}
    assert await scalar("SELECT github_repo_id FROM repositories WHERE is_selected") == 2


async def test_saving_the_same_selection_twice_changes_nothing(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    body = {"select": [ids["repo-1"]]}
    await browser.post("/api/repositories/selection", json=body)
    first_time = await scalar("SELECT selected_at FROM repositories WHERE is_selected")

    again = await browser.post("/api/repositories/selection", json=body)

    assert again.json() == {"selected_count": 1}
    assert await scalar("SELECT selected_at FROM repositories WHERE is_selected") == first_time


async def test_an_empty_save_is_harmless(browser):
    await connected_with_repositories(browser)

    response = await browser.post("/api/repositories/selection", json={})

    assert response.status_code == 200
    assert response.json() == {"selected_count": 0}


# --- Scenario: DevPulse fetches pull request data right after the selection is saved ----------------


async def test_saving_a_new_selection_queues_the_pull_request_job_right_away(browser, dispatcher):
    connection_id = await connected_with_repositories(browser)
    ids = await ids_by_name(browser)

    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"], ids["repo-2"]]})

    # One job for the connection, carrying only its internal ID and why it was queued.
    assert dispatcher.pull_request_calls == [(connection_id, "selection_saved")]


async def test_unselecting_only_does_not_queue_a_job(browser, dispatcher):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})
    dispatcher.pull_request_calls.clear()

    await browser.post("/api/repositories/selection", json={"unselect": [ids["repo-1"]]})

    assert dispatcher.pull_request_calls == []


async def test_saving_the_same_selection_again_does_not_queue_another_job(browser, dispatcher):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    body = {"select": [ids["repo-1"]]}
    await browser.post("/api/repositories/selection", json=body)
    dispatcher.pull_request_calls.clear()

    await browser.post("/api/repositories/selection", json=body)

    assert dispatcher.pull_request_calls == []


async def test_a_rejected_save_queues_nothing(browser, dispatcher):
    await connected_with_repositories(browser)
    dispatcher.pull_request_calls.clear()

    response = await browser.post("/api/repositories/selection", json={"select": [str(uuid.uuid4())]})

    assert response.status_code == 404
    assert dispatcher.pull_request_calls == []


async def test_the_selection_is_saved_even_if_the_job_cannot_be_queued(browser, dispatcher):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    dispatcher.can_queue = False

    response = await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})

    assert response.status_code == 200
    assert response.json() == {"selected_count": 1}


# --- Scenario: I stop tracking a repository --------------------------------------------------------


async def test_unselecting_keeps_the_repository_and_selecting_it_again_brings_it_back(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})
    row_id = await scalar("SELECT id FROM repositories WHERE github_repo_id = 1")

    off = await browser.post("/api/repositories/selection", json={"unselect": [ids["repo-1"]]})

    assert off.json() == {"selected_count": 0}
    assert await scalar("SELECT count(*) FROM repositories") == 3  # nothing deleted
    assert await scalar("SELECT selected_at IS NULL FROM repositories WHERE github_repo_id = 1") is True

    on = await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})

    assert on.json() == {"selected_count": 1}
    assert await scalar("SELECT id FROM repositories WHERE github_repo_id = 1") == row_id  # the same row


async def test_the_selection_survives_a_refresh_of_the_repository_list(browser):
    connection_id = await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})

    # The background job runs again: the repository is renamed, another one disappears.
    async with SessionLocal() as session:
        repository = RepositoryRepository(session)
        await repository.upsert_many(connection_id=connection_id, repositories=[repo(1, "renamed")], now=datetime.now(UTC))
        await repository.mark_missing_unavailable(connection_id=connection_id, seen_github_ids=[1], now=datetime.now(UTC))
        await session.commit()

    body = await listing(browser)

    assert [(i["full_name"], i["is_selected"]) for i in body["items"]] == [("octocat/renamed", True)]


async def test_a_repository_that_returns_to_github_is_still_selected(browser):
    connection_id = await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-2"]]})
    async with SessionLocal() as session:
        repository = RepositoryRepository(session)
        await repository.mark_missing_unavailable(connection_id=connection_id, seen_github_ids=[1, 3], now=datetime.now(UTC))
        await session.commit()
    assert (await listing(browser))["selected_count"] == 0  # hidden while unavailable

    await store_repositories(connection_id, [repo(1), repo(2), repo(3)])

    assert (await listing(browser))["selected_count"] == 1


# --- Validation, ownership and safety -------------------------------------------------------------


async def test_selecting_requires_a_signed_in_user(browser):
    response = await browser.post("/api/repositories/selection", json={"select": [str(uuid.uuid4())]})

    assert response.status_code == 401


async def test_selecting_needs_a_connection(browser):
    await sign_in(browser)

    response = await browser.post("/api/repositories/selection", json={"select": [str(uuid.uuid4())]})

    assert response.status_code == 409
    assert response.json()["code"] == "not_connected"


async def test_selecting_from_another_origin_is_rejected(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)

    response = await browser.post(
        "/api/repositories/selection",
        json={"select": [ids["repo-1"]]},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert (await listing(browser))["selected_count"] == 0


async def test_a_repository_cannot_be_selected_and_unselected_at_once(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)

    response = await browser.post(
        "/api/repositories/selection",
        json={"select": [ids["repo-1"]], "unselect": [ids["repo-1"]]},
    )

    assert response.status_code == 422


async def test_malformed_and_oversized_requests_are_rejected(browser):
    await connected_with_repositories(browser)

    bad_id = await browser.post("/api/repositories/selection", json={"select": ["not-a-uuid"]})
    too_many = await browser.post(
        "/api/repositories/selection", json={"select": [str(uuid.uuid4()) for _ in range(501)]}
    )

    assert bad_id.status_code == too_many.status_code == 422


async def test_an_unknown_repository_is_rejected_and_nothing_is_saved(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)

    response = await browser.post(
        "/api/repositories/selection",
        json={"select": [ids["repo-1"], str(uuid.uuid4())]},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "repository_not_found"
    assert (await listing(browser))["selected_count"] == 0  # the valid one was not applied either


async def test_another_users_repository_is_rejected_like_an_unknown_one(
    new_browser: Browser, github: FakeGitHub
):
    mine, theirs = new_browser(), new_browser()
    await connected_with_repositories(mine)
    github.user = {**github.user, "id": 2002, "login": "other"}
    github.installations[6002] = make_installation(6002, account_id=2002, login="other")
    await sign_in(theirs)
    await connect(theirs, installation_id=6002)
    their_connection = await scalar("SELECT id FROM github_connections WHERE installation_id = 6002")
    await store_repositories(their_connection, [repo(10, "private-one")])
    their_repo_id = await scalar("SELECT id FROM repositories WHERE github_repo_id = 10")

    response = await mine.post("/api/repositories/selection", json={"select": [str(their_repo_id)]})

    assert response.status_code == 404
    assert response.json()["code"] == "repository_not_found"
    assert await scalar("SELECT is_selected FROM repositories WHERE github_repo_id = 10") is False


async def test_users_only_ever_see_their_own_repositories(new_browser: Browser, github: FakeGitHub):
    mine, theirs = new_browser(), new_browser()
    await connected_with_repositories(mine)
    github.user = {**github.user, "id": 2002, "login": "other"}
    github.installations[6002] = make_installation(6002, account_id=2002, login="other")
    await sign_in(theirs)
    await connect(theirs, installation_id=6002)
    their_connection = await scalar("SELECT id FROM github_connections WHERE installation_id = 6002")
    await store_repositories(their_connection, [repo(10, "private-one")])

    names = [i["full_name"] for i in (await listing(mine))["items"]]

    assert "octocat/private-one" not in names
    assert (await listing(mine))["total"] == 3


async def test_a_repository_the_app_lost_access_to_cannot_be_selected_but_can_be_dropped(browser):
    await connected_with_repositories(browser)
    ids = await ids_by_name(browser)
    await browser.post("/api/repositories/selection", json={"select": [ids["repo-1"]]})
    async with SessionLocal() as session:
        await session.execute(text("UPDATE repositories SET is_available = false WHERE github_repo_id IN (1, 2)"))
        await session.commit()

    cannot_select = await browser.post("/api/repositories/selection", json={"select": [ids["repo-2"]]})
    can_drop = await browser.post("/api/repositories/selection", json={"unselect": [ids["repo-1"]]})

    assert cannot_select.status_code == 409
    assert cannot_select.json()["code"] == "repository_unavailable"
    assert can_drop.status_code == 200
    assert await scalar("SELECT is_selected FROM repositories WHERE github_repo_id = 1") is False
    assert await scalar("SELECT is_selected FROM repositories WHERE github_repo_id = 2") is False


async def test_error_responses_are_safe(browser):
    await connected_with_repositories(browser)

    response = await browser.post("/api/repositories/selection", json={"select": [str(uuid.uuid4())]})

    assert set(response.json()) == {"code", "message"}
    assert ORIGIN not in response.text
