"""Domain-specific exception types for the phone-address service."""


class EntityAlreadyExists(Exception):
    """Raised when attempting to create an entity that already exists."""


class EntityNotFound(Exception):
    """Raised when an entity cannot be found in the underlying storage."""

