"""Application services for tenant-scoped agent memory."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = frozenset(
    {
        "email",
        "email_address",
        "phone",
        "phone_number",
        "mobile",
        "mobile_number",
        "address",
        "street_address",
        "postal_address",
        "customer_address",
        "customer_email",
        "customer_phone",
        "customer_name",
        "first_name",
        "last_name",
        "full_name",
        "date_of_birth",
        "dob",
        "ssn",
        "social_security_number",
        "national_id",
        "passport_number",
        "credit_card",
        "credit_card_number",
        "card_number",
    }
)


def redact_memory_value(value: Any) -> Any:
    """Recursively redact explicitly sensitive mapping keys."""
    if isinstance(value, Mapping):
        return {
            key: (
                _REDACTED
                if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS
                else redact_memory_value(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_memory_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_memory_value(item) for item in value)

    return value


__all__ = ["redact_memory_value"]
