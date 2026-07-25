"""Dynamic validator plugin discovery."""
from __future__ import annotations
import importlib, inspect, pkgutil
from validators.base import CategoryValidator


class ValidatorRegistry:
    def __init__(self, package: str = "validators") -> None:
        self._validators: dict[str, CategoryValidator] = {}
        root = importlib.import_module(package)
        for info in pkgutil.iter_modules(root.__path__, f"{package}."):
            module = importlib.import_module(info.name)
            for _, candidate in inspect.getmembers(module, inspect.isclass):
                if candidate is not CategoryValidator and issubclass(candidate, CategoryValidator):
                    instance = candidate(); self._validators[instance.category] = instance
    def get(self, category: str) -> CategoryValidator: return self._validators[category]
    def categories(self) -> list[str]: return sorted(self._validators)
