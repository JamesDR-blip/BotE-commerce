"""Base contracts for validator plugins."""
from __future__ import annotations

from abc import ABC

from validators.base import CategoryValidator


class ValidatorPlugin(CategoryValidator, ABC):
    """Marker base class for validators distributed as plugins.

    It deliberately adds no validation behavior. Existing category validators
    and plugin validators therefore share exactly the same execution contract.
    """


__all__ = ["ValidatorPlugin"]
