"""Application entrypoint for the phone-address directory microservice."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from .api.health import router as health_router
from .api.v1.endpoints.address import router as address_router
from .core.config import get_settings
from .core.database import get_redis_client
from .core.exceptions import EntityAlreadyExists, EntityNotFound
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


@app.exception_handler(EntityAlreadyExists)
async def handle_entity_already_exists(
        request: Request, exc: EntityAlreadyExists
) -> JSONResponse:
    """Map EntityAlreadyExists to a sanitized HTTP 409 Conflict response."""

    return JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "message": "A record with this phone number already exists.",
        },
    )


@app.exception_handler(EntityNotFound)
async def handle_entity_not_found(
        request: Request, exc: EntityNotFound
) -> JSONResponse:
    """Map EntityNotFound to a sanitized HTTP 404 Not Found response."""

    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "The requested phone number was not found.",
        },
    )


app.include_router(health_router)
app.include_router(address_router)
