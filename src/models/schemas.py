"""Pydantic models and validation schemas for the API."""

from pydantic import BaseModel, Field, field_validator

from src.core.utils import normalize_phone


class AddressCreate(BaseModel):
    """Request body for creating a new phone→address mapping."""

    phone: str = Field(..., description="Phone number to associate with the address.")
    address: str = Field(..., min_length=1, description="Non-empty address string.")

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str) -> str:
        """Normalize and validate the phone number using shared helper logic."""

        return normalize_phone(value)


class AddressUpdate(BaseModel):
    """Request body for updating an existing address."""

    address: str = Field(..., min_length=1, description="New non-empty address value.")


class AddressResponse(BaseModel):
    """Response model representing a stored phone→address mapping."""

    phone: str
    address: str


class PhonePathParam(BaseModel):
    """Model for validating and normalizing phone numbers in URL path parameters."""

    phone: str

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str) -> str:
        """Normalize and validate the phone number using shared helper logic."""

        return normalize_phone(value)

