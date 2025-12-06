"""Application configuration and settings management."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings loaded from environment variables.

    Redis configuration is sourced from:
      * APP_REDIS_HOST
      * APP_REDIS_PORT
      * APP_REDIS_DB
    """

    # Removing the default makes this required; the app will fail fast if
    # APP_REDIS_HOST is not provided in the environment or .env file.
    redis_host: str = Field(..., description="Redis hostname is required")
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    # noinspection PyArgumentList
    return Settings()
