import httpx
import pytest

from app.github_integration.client import GitHubClient
from app.github_integration.errors import GitHubAuthorizationError, GitHubUnavailableError
from tests.fake_github import FAKE_USER_TOKEN, GOOD_CODE, FakeGitHub

REDIRECT = "http://localhost:5173/api/auth/github/callback"


def make_client(handler) -> GitHubClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GitHubClient(client_id="cid", client_secret="csecret", http=http)


async def test_authorize_url_carries_client_state_and_callback_only():
    client = make_client(FakeGitHub().handler)

    url = client.authorize_url(state="abc", redirect_uri=REDIRECT)

    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=cid" in url and "state=abc" in url
    assert "csecret" not in url


async def test_exchange_code_returns_user_token():
    client = make_client(FakeGitHub().handler)

    assert await client.exchange_code(code=GOOD_CODE, redirect_uri=REDIRECT) == FAKE_USER_TOKEN


async def test_exchange_code_rejects_a_bad_or_reused_code():
    client = make_client(FakeGitHub().handler)

    with pytest.raises(GitHubAuthorizationError):
        await client.exchange_code(code="reused", redirect_uri=REDIRECT)


async def test_exchange_code_maps_github_outage_and_network_errors_to_unavailable():
    fake = FakeGitHub()
    fake.unavailable = True
    with pytest.raises(GitHubUnavailableError):
        await make_client(fake.handler).exchange_code(code=GOOD_CODE, redirect_uri=REDIRECT)

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=request)

    with pytest.raises(GitHubUnavailableError):
        await make_client(timeout).exchange_code(code=GOOD_CODE, redirect_uri=REDIRECT)


async def test_get_user_keeps_only_the_fields_devpulse_needs():
    fake = FakeGitHub()
    fake.user = {**fake.user, "plan": {"name": "pro"}, "two_factor_authentication": True}

    user = await make_client(fake.handler).get_authenticated_user(FAKE_USER_TOKEN)

    assert user.model_dump() == {
        "id": 1001,
        "login": "octocat",
        "name": "The Octocat",
        "avatar_url": "https://avatars.example/octocat.png",
        "email": "octocat@example.com",
    }


async def test_get_user_allows_a_missing_email_and_name():
    fake = FakeGitHub()
    fake.user = {"id": 7, "login": "quiet", "name": None, "avatar_url": None, "email": None}

    user = await make_client(fake.handler).get_authenticated_user(FAKE_USER_TOKEN)

    assert user.email is None and user.name is None


async def test_get_user_rejects_an_invalid_token():
    with pytest.raises(GitHubAuthorizationError):
        await make_client(FakeGitHub().handler).get_authenticated_user("ghu_wrong")


async def test_get_user_treats_rate_limiting_as_unavailable_not_as_bad_credentials():
    def limited(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, headers={"x-ratelimit-remaining": "0"}, json={})

    with pytest.raises(GitHubUnavailableError):
        await make_client(limited).get_authenticated_user(FAKE_USER_TOKEN)


async def test_get_user_treats_an_unusable_response_as_unavailable():
    def garbage(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    with pytest.raises(GitHubUnavailableError):
        await make_client(garbage).get_authenticated_user(FAKE_USER_TOKEN)


async def test_error_text_never_contains_the_token():
    with pytest.raises(GitHubAuthorizationError) as raised:
        await make_client(FakeGitHub().handler).get_authenticated_user("ghu_wrong_token_value")

    assert "ghu_wrong_token_value" not in str(raised.value)
