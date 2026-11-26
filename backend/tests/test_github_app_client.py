import jwt
import httpx
import pytest

from app.common.errors import NotConfiguredError
from app.github_integration.client import GitHubClient
from app.github_integration.errors import (
    GitHubAccessError,
    GitHubRateLimitedError,
    GitHubUnavailableError,
)
from tests.fake_github import (
    FAKE_INSTALLATION_TOKEN,
    FakeGitHub,
    make_installation,
    make_repo,
)
from tests.keys import APP_ID, APP_SLUG, PRIVATE_KEY_PATH, PUBLIC_KEY_PEM


def make_client(handler, *, key_path: str = str(PRIVATE_KEY_PATH)) -> GitHubClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GitHubClient(
        client_id="cid",
        client_secret="csecret",
        http=http,
        app_id=APP_ID,
        app_slug=APP_SLUG,
        private_key_path=key_path,
    )


def reply(status: int, headers: dict | None = None, body: dict | None = None):
    return lambda request: httpx.Response(status, headers=headers or {}, json=body or {})


# --- Setup ----------------------------------------------------------------------


async def test_app_is_not_configured_without_a_readable_private_key():
    client = make_client(FakeGitHub().handler, key_path="/does/not/exist.pem")

    assert client.is_app_configured is False
    with pytest.raises(NotConfiguredError):
        await client.get_installation(5001)


async def test_install_url_points_at_the_apps_install_page_with_the_state():
    client = make_client(FakeGitHub().handler)

    assert client.install_url(state="abc") == (
        f"https://github.com/apps/{APP_SLUG}/installations/new?state=abc"
    )


# --- App JWT ----------------------------------------------------------------------


async def test_app_requests_carry_a_short_lived_jwt_signed_with_the_private_key():
    fake = FakeGitHub()

    await make_client(fake.handler).get_installation(5001)

    bearer = fake.api_calls("/app/installations/5001")[0].headers["authorization"].removeprefix("Bearer ")
    claims = jwt.decode(bearer, PUBLIC_KEY_PEM, algorithms=["RS256"])
    assert claims["iss"] == APP_ID
    assert 0 < claims["exp"] - claims["iat"] <= 600  # GitHub allows at most 10 minutes


async def test_a_rejected_app_token_is_a_configuration_problem_not_revoked_access():
    with pytest.raises(NotConfiguredError):
        await make_client(reply(401, body={"message": "A JSON web token could not be decoded"})).get_installation(1)


# --- Installation lookup ------------------------------------------------------------


async def test_installation_keeps_only_what_devpulse_needs():
    fake = FakeGitHub()
    fake.installations[5001] = {**make_installation(), "app_slug": "x", "events": ["a"], "html_url": "u"}

    installation = await make_client(fake.handler).get_installation(5001)

    assert installation.model_dump() == {
        "id": 5001,
        "account_id": 1001,
        "account_login": "octocat",
        "account_type": "User",
        "permissions": {"metadata": "read", "pull_requests": "read"},
        "suspended": False,
    }


async def test_a_suspended_installation_is_flagged():
    fake = FakeGitHub()
    fake.installations[5001] = make_installation(suspended=True)

    assert (await make_client(fake.handler).get_installation(5001)).suspended is True


async def test_an_unknown_installation_means_access_was_revoked():
    with pytest.raises(GitHubAccessError) as raised:
        await make_client(FakeGitHub().handler).get_installation(9999)

    assert raised.value.reason == "access_revoked"


# --- Installation token -----------------------------------------------------------


async def test_installation_token_is_requested_with_read_only_permissions_only():
    fake = FakeGitHub()

    token = await make_client(fake.handler).create_installation_token(5001)

    request = fake.api_calls("/app/installations/5001/access_tokens")[0]
    assert token == FAKE_INSTALLATION_TOKEN
    assert request.method == "POST"
    assert httpx.Response(200, content=request.content).json() == {
        "permissions": {"metadata": "read", "pull_requests": "read"}
    }


@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        ("missing", "access_revoked"),
        ("suspended", "suspended"),
        ("no_pull_requests", "permission_missing"),
    ],
)
async def test_token_failures_are_mapped_to_a_fixed_reason(setup, reason):
    fake = FakeGitHub()
    if setup == "suspended":
        fake.installations[5001] = make_installation(suspended=True)
    if setup == "no_pull_requests":
        fake.installations[5001] = make_installation(permissions={"metadata": "read"})
    installation_id = 9999 if setup == "missing" else 5001

    with pytest.raises(GitHubAccessError) as raised:
        await make_client(fake.handler).create_installation_token(installation_id)

    assert raised.value.reason == reason


# --- Repository list ------------------------------------------------------------------


async def test_all_pages_of_repositories_are_read():
    fake = FakeGitHub()
    fake.repositories = [make_repo(i) for i in range(1, 251)]  # 100 + 100 + 50

    repos = await make_client(fake.handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert [r.id for r in repos] == list(range(1, 251))
    assert len(fake.api_calls("/installation/repositories")) == 3


async def test_a_page_that_is_exactly_full_is_followed_by_one_more_request():
    fake = FakeGitHub()
    fake.repositories = [make_repo(i) for i in range(1, 101)]

    repos = await make_client(fake.handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert len(repos) == 100
    assert len(fake.api_calls("/installation/repositories")) == 2


async def test_an_installation_with_no_repositories_gives_an_empty_list():
    fake = FakeGitHub()
    fake.repositories = []

    assert await make_client(fake.handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN) == []


async def test_repositories_keep_identity_fields_only():
    fake = FakeGitHub()
    fake.repositories = [make_repo(7, "api", owner="octocat", private=True)]

    (repo,) = await make_client(fake.handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert repo.model_dump() == {
        "id": 7,
        "name": "api",
        "full_name": "octocat/api",
        "owner_login": "octocat",
        "is_private": True,
    }


async def test_an_expired_installation_token_is_access_revoked():
    with pytest.raises(GitHubAccessError) as raised:
        await make_client(FakeGitHub().handler).list_installation_repositories("ghs_expired")

    assert raised.value.reason == "access_revoked"


async def test_a_permission_error_on_the_list_is_permission_missing():
    handler = reply(403, body={"message": "Resource not accessible by integration"})

    with pytest.raises(GitHubAccessError) as raised:
        await make_client(handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert raised.value.reason == "permission_missing"


# --- Rate limits and outages ----------------------------------------------------------


async def test_a_primary_rate_limit_reports_how_long_to_wait():
    import time

    reset = int(time.time()) + 120
    handler = reply(403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(reset)}, {"message": "API rate limit exceeded"})

    with pytest.raises(GitHubRateLimitedError) as raised:
        await make_client(handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert 100 <= raised.value.retry_after <= 120
    assert raised.value.reset_at is not None


async def test_a_secondary_rate_limit_honours_retry_after():
    handler = reply(429, {"retry-after": "45"}, {"message": "secondary rate limit"})

    with pytest.raises(GitHubRateLimitedError) as raised:
        await make_client(handler).list_installation_repositories(FAKE_INSTALLATION_TOKEN)

    assert raised.value.retry_after == 45


async def test_rate_limiting_counts_as_temporary_so_it_is_retried():
    assert issubclass(GitHubRateLimitedError, GitHubUnavailableError)


@pytest.mark.parametrize("status", [500, 502, 503])
async def test_github_server_errors_are_temporary(status):
    with pytest.raises(GitHubUnavailableError):
        await make_client(reply(status)).list_installation_repositories(FAKE_INSTALLATION_TOKEN)


async def test_network_failures_are_temporary():
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=request)

    with pytest.raises(GitHubUnavailableError):
        await make_client(timeout).create_installation_token(5001)


async def test_an_unusable_repository_response_is_temporary_not_a_crash():
    with pytest.raises(GitHubUnavailableError):
        await make_client(reply(200, body={"unexpected": True})).list_installation_repositories(
            FAKE_INSTALLATION_TOKEN
        )


async def test_error_text_never_contains_a_token_or_the_private_key():
    errors: list[Exception] = []
    for call in (
        lambda c: c.list_installation_repositories(FAKE_INSTALLATION_TOKEN),
        lambda c: c.create_installation_token(5001),
    ):
        try:
            await call(make_client(reply(503)))
        except GitHubUnavailableError as exc:
            errors.append(exc)

    text = " ".join(f"{e!r} {e}" for e in errors)
    assert FAKE_INSTALLATION_TOKEN not in text
    assert "BEGIN" not in text
