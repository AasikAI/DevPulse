from fastapi import Request

from app.github_integration.client import GitHubClient


def get_github_client(request: Request) -> GitHubClient:
    # Created once at startup in main.py's lifespan; tests override this dependency.
    return request.app.state.github_client
