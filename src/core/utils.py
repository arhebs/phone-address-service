"""Core utility functions for the phone-address service."""

from phonenumbers import NumberParseException, PhoneNumberFormat, is_valid_number, parse, format_number

DEFAULT_REGION = "US"


def normalize_phone(phone: str) -> str:
    """Normalize a phone number to E.164 format (e.g., +15551234567).

    The normalization rules are:
    - Parse the phone number using the default region (US) when no country code
      is present, while still supporting fully-qualified international numbers
      (e.g. starting with ``+``).
    - Validate the parsed number using libphonenumber's rules.
    - Format the resulting number in E.164 format.

    A ``ValueError`` is raised if the input does not represent a valid phone
    number.
    """

    try:
        parsed = parse(phone, DEFAULT_REGION)
    except NumberParseException as exc:
        raise ValueError("Invalid phone number.") from exc

    if not is_valid_number(parsed):
        raise ValueError("Invalid phone number.")

    return format_number(parsed, PhoneNumberFormat.E164)

