from functools import lru_cache
from secrets import token_urlsafe

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Repo Guardian API"
    app_version: str = "0.1.0"
    database_url: str
    frontend_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    frontend_url: str = "http://localhost:8080"
    github_client_id: str | None = None
    github_client_secret: SecretStr | None = None
    github_oauth_callback_url: str = "http://localhost:8000/api/auth/github/callback"
    github_webhook_secret: SecretStr | None = None
    github_app_id: int | None = None
    github_app_slug: str | None = None
    github_app_private_key_base64: SecretStr | None = None
    token_encryption_key: SecretStr | None = None
    session_secret: SecretStr = Field(
        default_factory=lambda: SecretStr(token_urlsafe(48))
    )
    session_cookie_secure: bool = False

    @field_validator("session_secret", mode="before")
    @classmethod
    def generate_development_session_secret(cls, value: object) -> object:
        if value in (None, ""):
            return token_urlsafe(48)
        return value

    @field_validator("github_app_id", mode="before")
    @classmethod
    def empty_optional_integer(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
