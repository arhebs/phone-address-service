"""Application entrypoint for the phone-address directory microservice."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from redis.asyncio import Redis

from .core.config import get_settings
from .core.database import get_redis_client
from .core.logging import configure_logging


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Initializes a shared Redis client and configures logging at startup,
    and ensures the Redis connection is closed on shutdown.
    """

    configure_logging()
    settings = get_settings()
    redis_client: Redis = get_redis_client(settings)

    # Attach the Redis client to application state for shared access.
    fastapi_app.state.redis = redis_client  # type: ignore[attr-defined]
    try:
        yield
    finally:
        await redis_client.close()


app = FastAPI(
    title="Phone Address Directory",
    version="1.0.0",
    description="Strict REST + Atomic Redis",
    lifespan=lifespan,
)
