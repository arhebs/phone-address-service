"""Healthcheck endpoint for liveness probes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Simple liveness check that does not touch external dependencies."""

    return {"status": "ok"}

