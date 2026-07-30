"""Dynamic discovery for validator plugins and legacy validators."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Sequence

from validators.base import CategoryValidator


class ValidatorRegistry:
    """Discover validators, prioritising plugin packages over legacy modules."""

    def __init__(self, packages: Sequence[str] = ("plugins", "validators")) -> None:
        self._validators: dict[str, CategoryValidator] = {}
        for package in packages:
            self._discover(package)

    def _discover(self, package: str) -> None:
        root = importlib.import_module(package)
        if not hasattr(root, "__path__"):
            raise ValueError(f"Plugin package '{package}' is not a package")
        for module_info in pkgutil.walk_packages(root.__path__, f"{package}."):
            module = importlib.import_module(module_info.name)
            for _, candidate in inspect.getmembers(module, inspect.isclass):
                if self._is_validator(candidate):
                    self._register(candidate())

    @staticmethod
    def _is_validator(candidate: object) -> bool:
        return (
            inspect.isclass(candidate)
            and candidate is not CategoryValidator
            and issubclass(candidate, CategoryValidator)
            and not inspect.isabstract(candidate)
        )

    def _register(self, validator: CategoryValidator) -> None:
        """Retain the first validator for a category (plugins load first)."""
        self._validators.setdefault(validator.category, validator)

    def get(self, category: str) -> CategoryValidator:
        return self._validators[category]

    def categories(self) -> list[str]:
        return sorted(self._validators)


__all__ = ["ValidatorRegistry"]
