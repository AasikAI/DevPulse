import httpx

# Obviously fake values, shaped like real ones so redaction rules apply to them.
FAKE_USER_TOKEN = "ghu_" + "FakeUserTokenForTests0123456789abcd"
GOOD_CODE = "good-code"


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
        self.unavailable = False
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.unavailable:
            return httpx.Response(503, json={"message": "unavailable"})

        if request.url.host == "github.com" and request.url.path == "/login/oauth/access_token":
            body = httpx.Response(200, content=request.content).json()
            if body.get("code") == GOOD_CODE:
                return httpx.Response(200, json={"access_token": FAKE_USER_TOKEN, "token_type": "bearer"})
            return httpx.Response(200, json={"error": "bad_verification_code"})

        if request.url.host == "api.github.com" and request.url.path == "/user":
            if request.headers.get("authorization") != f"Bearer {FAKE_USER_TOKEN}":
                return httpx.Response(401, json={"message": "Bad credentials"})
            return httpx.Response(200, json=self.user)

        return httpx.Response(404)
