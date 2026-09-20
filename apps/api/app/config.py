from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://egyxos:change-me@localhost:5432/egyxos"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = Field(default="development-only-change-this-secret", min_length=32)
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 30, ge=300)
    web_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
