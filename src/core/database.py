"""Redis client construction utilities."""

from typing import Final

from redis.asyncio import Redis, from_url

from .config import Settings

REDIS_SCHEME: Final[str] = "redis"


def build_redis_dsn(settings: Settings) -> str:
    """Build a Redis connection URL from the given settings."""

    return f"{REDIS_SCHEME}://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_redis_client(settings: Settings) -> Redis:
    """Create and return a Redis client instance."""

    dsn = build_redis_dsn(settings)
    return from_url(dsn, encoding="utf-8", decode_responses=True)

