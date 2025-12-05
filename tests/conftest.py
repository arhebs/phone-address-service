"""Test configuration and fixtures for the phone-address service."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from src.core.config import get_settings
from src.core.database import get_redis_client
from src.main import app as fastapi_app


@pytest.fixture
def app() -> FastAPI:
    """Return the FastAPI application instance with Redis initialized."""

    settings = get_settings()
    redis_client = get_redis_client(settings)
    fastapi_app.state.redis = redis_client  # type: ignore[attr-defined]
    return fastapi_app


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    """Provide an AsyncClient bound to the FastAPI application."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def clear_redis(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Automatically clear Redis before and after each test."""

    redis: Redis = app.state.redis  # type: ignore[attr-defined]
    await redis.flushdb()
    try:
        yield
    finally:
        await redis.flushdb()
