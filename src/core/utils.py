"""Core utility functions for the phone-address service."""


def normalize_phone(phone: str) -> str:
    """Normalize a phone number by stripping non-digits and validating length.

    The normalization rules are:
    - Remove all non-digit characters.
    - Require between 7 and 15 digits (inclusive).

    A ``ValueError`` is raised if the input does not satisfy the constraints.
    """

    digits_only = "".join(ch for ch in phone if ch.isdigit())
    length = len(digits_only)

    if length < 7 or length > 15:
        raise ValueError("Phone number must contain between 7 and 15 digits.")

    return digits_only

