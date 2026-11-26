import re

import httpx

# Obviously fake values, shaped like real ones so redaction rules apply to them.
FAKE_USER_TOKEN = "ghu_" + "FakeUserTokenForTests0123456789abcd"
FAKE_INSTALLATION_TOKEN = "ghs_" + "FakeInstallationTokenForTests0123456789"
GOOD_CODE = "good-code"

FULL_PERMISSIONS = {"metadata": "read", "pull_requests": "read"}


def make_repo(repo_id: int, name: str | None = None, owner: str = "octocat", private: bool = False) -> dict:
    name = name or f"repo-{repo_id}"
    return {
        "id": repo_id,
        "name": name,
        "full_name": f"{owner}/{name}",
        "private": private,
        "owner": {"login": owner},
        # Extra fields GitHub sends; the client must ignore them.
        "description": "not stored",
        "default_branch": "main",
    }


def make_installation(
    installation_id: int = 5001,
    account_id: int = 1001,
    login: str = "octocat",
    account_type: str = "User",
    permissions: dict | None = None,
    suspended: bool = False,
) -> dict:
    return {
        "id": installation_id,
        "account": {"id": account_id, "login": login, "type": account_type},
        "permissions": FULL_PERMISSIONS if permissions is None else permissions,
        "suspended_at": "2026-11-01T00:00:00Z" if suspended else None,
    }


class FakeGitHub:
    """Stands in for github.com and api.github.com behind an httpx MockTransport."""

    def __init__(self) -> None:
        self.user: dict = {
            "id": 1001,
            "login": "octocat",
            "name": "The Octocat",
            "avatar_url": "https://avatars.example/octocat.png",
            "email": "octocat@example.com",
        }
        self.installations: dict[int, dict] = {5001: make_installation()}
        self.repositories: list[dict] = [make_repo(1), make_repo(2), make_repo(3, private=True)]
        self.unavailable = False
        # When set, installation endpoints answer with this status and optional headers.
        self.installation_error: tuple[int, dict, dict] | None = None
        self.token_error: tuple[int, dict, dict] | None = None
        self.repositories_error_on_page: tuple[int, int] | None = None
        self.requests: list[httpx.Request] = []

    def api_calls(self, path_prefix: str) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.path.startswith(path_prefix)]

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.unavailable:
            return httpx.Response(503, json={"message": "unavailable"})

        path = request.url.path
        if request.url.host == "github.com" and path == "/login/oauth/access_token":
            body = httpx.Response(200, content=request.content).json()
            if body.get("code") == GOOD_CODE:
                return httpx.Response(200, json={"access_token": FAKE_USER_TOKEN, "token_type": "bearer"})
            return httpx.Response(200, json={"error": "bad_verification_code"})

        if request.url.host != "api.github.com":
            return httpx.Response(404)

        if path == "/user":
            if request.headers.get("authorization") != f"Bearer {FAKE_USER_TOKEN}":
                return httpx.Response(401, json={"message": "Bad credentials"})
            return httpx.Response(200, json=self.user)

        installation = re.fullmatch(r"/app/installations/(\d+)", path)
        if installation and request.method == "GET":
            if self.installation_error:
                status, headers, body = self.installation_error
                return httpx.Response(status, headers=headers, json=body)
            found = self.installations.get(int(installation.group(1)))
            if found is None:
                return httpx.Response(404, json={"message": "Not Found"})
            return httpx.Response(200, json=found)

        token = re.fullmatch(r"/app/installations/(\d+)/access_tokens", path)
        if token and request.method == "POST":
            if self.token_error:
                status, headers, body = self.token_error
                return httpx.Response(status, headers=headers, json=body)
            found = self.installations.get(int(token.group(1)))
            if found is None:
                return httpx.Response(404, json={"message": "Not Found"})
            if found["suspended_at"]:
                return httpx.Response(403, json={"message": "This GitHub App installation is suspended."})
            if "pull_requests" not in found["permissions"]:
                return httpx.Response(422, json={"message": "The permissions requested are not granted"})
            return httpx.Response(201, json={"token": FAKE_INSTALLATION_TOKEN, "expires_at": "2026-11-26T12:00:00Z"})

        if path == "/installation/repositories":
            if request.headers.get("authorization") != f"Bearer {FAKE_INSTALLATION_TOKEN}":
                return httpx.Response(401, json={"message": "Bad credentials"})
            page = int(request.url.params.get("page", "1"))
            per_page = int(request.url.params.get("per_page", "30"))
            if self.repositories_error_on_page == (page, 503):
                return httpx.Response(503, json={"message": "unavailable"})
            start = (page - 1) * per_page
            return httpx.Response(
                200,
                headers={"x-ratelimit-remaining": "4990"},
                json={
                    "total_count": len(self.repositories),
                    "repositories": self.repositories[start : start + per_page],
                },
            )

        return httpx.Response(404)
