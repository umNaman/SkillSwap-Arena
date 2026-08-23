from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/skillswap"
    SECRET_KEY: str = "placeholder_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AGORA_APP_ID: str = ""
    AGORA_APP_CERTIFICATE: str = ""
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: list[str] = ["*"]
    GD_ROUND_DURATION: int = 900
    MAX_SEATS: int = 6

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
