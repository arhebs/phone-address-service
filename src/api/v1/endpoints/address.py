"""Address management endpoints for version 1 of the API."""

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis

from src.core.deps import get_redis
from src.models.schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    PhonePathParam,
)
from src.services.address_service import AddressService

router = APIRouter(prefix="/v1/address", tags=["address"])


@router.get(
    "/{phone}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def get_address(
        phone_param: PhonePathParam = Depends(),
        redis: Redis = Depends(get_redis),
) -> AddressResponse:
    """Retrieve the address associated with the given phone number."""

    service = AddressService(redis)
    return await service.get(phone=phone_param.phone)


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
        payload: AddressCreate,
        redis: Redis = Depends(get_redis),
) -> AddressResponse:
    """Create a new phone→address mapping."""

    service = AddressService(redis)
    await service.create(phone=payload.phone, address=payload.address)
    return AddressResponse(phone=payload.phone, address=payload.address)


@router.put(
    "/{phone}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
)
async def update_address(
        phone_param: PhonePathParam = Depends(),
        payload: AddressUpdate | None = None,
        redis: Redis = Depends(get_redis),
) -> AddressResponse:
    """Update an existing phone→address mapping."""

    # payload is required, but annotated as optional to keep FastAPI type hints
    # flexible in case of future validation changes.
    assert payload is not None
    service = AddressService(redis)
    await service.update(phone=phone_param.phone, address=payload.address)
    return AddressResponse(phone=phone_param.phone, address=payload.address)


@router.delete(
    "/{phone}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_address(
        phone_param: PhonePathParam = Depends(),
        redis: Redis = Depends(get_redis),
) -> None:
    """Delete an existing phone→address mapping."""

    service = AddressService(redis)
    await service.delete(phone=phone_param.phone)
