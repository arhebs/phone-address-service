"""FastAPI dependency definitions for shared resources."""

from collections.abc import AsyncGenerator

from fastapi import Request
from redis.asyncio import Redis


async def get_redis(request: Request) -> AsyncGenerator[Redis, None]:
    """Yield the shared Redis client stored on the FastAPI app state."""

    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RuntimeError("Redis client is not initialized on application state.")

    yield redis
