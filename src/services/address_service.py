"""Service layer for phone→address mappings backed by Redis."""

import json
import logging
from typing import Final

from redis.asyncio import Redis

from src.core.exceptions import EntityAlreadyExists, EntityNotFound
from src.models.schemas import AddressResponse

logger = logging.getLogger(__name__)

_ADDRESS_KEY_PREFIX: Final[str] = "address:"


def _build_key(phone: str) -> str:
    """Build the Redis key for a given normalized phone number."""

    return f"{_ADDRESS_KEY_PREFIX}{phone}"


class AddressService:
    """Service providing CRUD operations for phone→address mappings."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def create(self, phone: str, address: str) -> None:
        """Create a new mapping if it does not already exist.

        Uses Redis `SET key value NX` to ensure atomic creation. Raises
        ``EntityAlreadyExists`` if the key is already present.
        """

        key = _build_key(phone)
        value = json.dumps({"address": address})

        logger.debug("Creating address mapping", extra={"phone": phone})
        created = await self._redis.set(key, value, nx=True)
        if not created:
            raise EntityAlreadyExists(f"Address for phone '{phone}' already exists.")

    async def get(self, phone: str) -> AddressResponse:
        """Retrieve an existing mapping.

        Raises ``EntityNotFound`` if the mapping is missing.
        """

        key = _build_key(phone)
        logger.debug("Fetching address mapping", extra={"phone": phone})
        raw = await self._redis.get(key)
        if raw is None:
            raise EntityNotFound(f"Address for phone '{phone}' not found.")

        data = json.loads(raw)
        address = data["address"]
        return AddressResponse(phone=phone, address=address)

    async def update(self, phone: str, address: str) -> None:
        """Update an existing mapping if it exists.

        Uses Redis `SET key value XX` to ensure atomic update of an existing
        record only. Raises ``EntityNotFound`` if the key does not exist.
        """

        key = _build_key(phone)
        value = json.dumps({"address": address})

        logger.debug("Updating address mapping", extra={"phone": phone})
        updated = await self._redis.set(key, value, xx=True)
        if not updated:
            raise EntityNotFound(f"Address for phone '{phone}' not found.")

    async def delete(self, phone: str) -> None:
        """Delete an existing mapping if present.

        Uses Redis ``DEL`` and raises ``EntityNotFound`` if no key was removed.
        """

        key = _build_key(phone)
        logger.debug("Deleting address mapping", extra={"phone": phone})
        deleted = await self._redis.delete(key)
        if deleted == 0:
            raise EntityNotFound(f"Address for phone '{phone}' not found.")

