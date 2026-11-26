from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # The single .env lives at the repo root and is shared with docker-compose.
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "DevPulse"
    environment: str = "development"

    # The browser only talks to this origin; Vite proxies /api to FastAPI.
    frontend_base_url: str = "http://localhost:5173"

    # Empty until the GitHub App is registered; sign-in then answers 503.
    github_app_client_id: str = ""
    github_app_client_secret: SecretStr = SecretStr("")

    # Needed from slice 2 on: connecting and reading data as the installed App.
    # The private key stays in a file outside the database and the repo.
    github_app_id: str = ""
    github_app_slug: str = ""
    github_app_private_key_path: str = ""

    redis_url: str = "redis://localhost:6379/0"

    session_lifetime_days: int = 14
    oauth_state_ttl_minutes: int = 10

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"

    @property
    def frontend_origin(self) -> str:
        return self.frontend_base_url.rstrip("/")

    @property
    def database_url(self) -> URL:
        # URL.create escapes special characters (e.g. '@') in the password.
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
