import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./skillswap.db"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AGORA_APP_ID: str = ""
    AGORA_APP_CERTIFICATE: str = ""
    AGORA_TOKEN_EXPIRE_SECONDS: int = 3600
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    CORS_ORIGINS: list[str] = ["*"]
    GD_ROUND_DURATION: int = 900
    GD_PREPARATION_DURATION: int = 120
    GD_DISCUSSION_DURATION: int = 780
    STALE_PRESTART_SESSION_SECONDS: int = 600
    STALE_IN_PROGRESS_GRACE_SECONDS: int = 300
    MAX_SEATS: int = 6
    PUBLIC_ROOM_POOL_SIZE: int = 3
    SEED_DEMO_DATA: bool = True
    JUDGE0_URL: str = ""
    JUDGE0_API_KEY: str = ""
    JUDGE0_API_HOST: str = ""
    JUDGE0_POLL_ATTEMPTS: int = 20
    JUDGE0_POLL_INTERVAL_MS: int = 250
    TURNSTILE_SITE_KEY: str = "1x00000000000000000000AA"  # Test key: always passes on localhost. Replace in prod.
    TURNSTILE_SECRET_KEY: str = "1x0000000000000000000000000000000AA"  # Test secret. Replace in prod.

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def ensure_secret_key(cls, value: str | None) -> str:
        if not value or value.lower().startswith(("your_", "placeholder")):
            return secrets.token_urlsafe(48)
        return value

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ignore_example_database_url(cls, value: str | None) -> str:
        if not value or "user:password@" in value.lower() or "placeholder" in value.lower():
            return "sqlite+aiosqlite:///./skillswap.db"
        return value

    @field_validator("AGORA_APP_ID", "AGORA_APP_CERTIFICATE", "OPENAI_API_KEY", mode="before")
    @classmethod
    def ignore_placeholder_credentials(cls, value: str | None) -> str:
        if not value or value.lower().startswith(("your_", "placeholder")):
            return ""
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
