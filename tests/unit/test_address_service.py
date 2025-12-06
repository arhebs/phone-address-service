"""Unit tests for the AddressService."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.core.exceptions import EntityAlreadyExists, EntityNotFound
from src.models.schemas import AddressResponse
from src.services.address_service import AddressService


@pytest.mark.asyncio
async def test_create_address_success() -> None:
    """Service should call Redis SET NX and succeed on first create."""

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=True)

    service = AddressService(mock_redis)
    await service.create("+15551234567", "123 Main St")

    mock_redis.set.assert_called_once_with(
        "address:+15551234567",
        '{"address": "123 Main St"}',
        nx=True,
    )


@pytest.mark.asyncio
async def test_create_address_conflict() -> None:
    """Service should raise EntityAlreadyExists when Redis NX fails."""

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=False)

    service = AddressService(mock_redis)

    with pytest.raises(EntityAlreadyExists):
        await service.create("+15551234567", "123 Main St")


@pytest.mark.asyncio
async def test_get_address_success() -> None:
    """Service should return AddressResponse when key exists."""

    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value='{"address": "123 Main St"}')

    service = AddressService(mock_redis)
    result = await service.get("+15551234567")

    mock_redis.get.assert_called_once_with("address:+15551234567")
    assert isinstance(result, AddressResponse)
    assert result.phone == "+15551234567"
    assert result.address == "123 Main St"


@pytest.mark.asyncio
async def test_get_address_not_found() -> None:
    """Service should raise EntityNotFound when key is missing."""

    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)

    service = AddressService(mock_redis)

    with pytest.raises(EntityNotFound):
        await service.get("+15551234567")


@pytest.mark.asyncio
async def test_update_address_success() -> None:
    """Service should call Redis SET XX on update."""

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=True)

    service = AddressService(mock_redis)
    await service.update("+15551234567", "Updated Address")

    mock_redis.set.assert_called_once_with(
        "address:+15551234567",
        '{"address": "Updated Address"}',
        xx=True,
    )


@pytest.mark.asyncio
async def test_update_address_not_found() -> None:
    """Service should raise EntityNotFound when updating missing key."""

    mock_redis = Mock()
    mock_redis.set = AsyncMock(return_value=False)

    service = AddressService(mock_redis)

    with pytest.raises(EntityNotFound):
        await service.update("+15551234567", "Updated Address")


@pytest.mark.asyncio
async def test_delete_address_success() -> None:
    """Service should call Redis DEL and succeed when key exists."""

    mock_redis = Mock()
    mock_redis.delete = AsyncMock(return_value=1)

    service = AddressService(mock_redis)
    await service.delete("+15551234567")

    mock_redis.delete.assert_called_once_with("address:+15551234567")


@pytest.mark.asyncio
async def test_delete_address_not_found() -> None:
    """Service should raise EntityNotFound when deleting missing key."""

    mock_redis = Mock()
    mock_redis.delete = AsyncMock(return_value=0)

    service = AddressService(mock_redis)

    with pytest.raises(EntityNotFound):
        await service.delete("+15551234567")

