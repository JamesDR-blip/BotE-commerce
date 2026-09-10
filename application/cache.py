"""Application-level cache contract."""
from __future__ import annotations

from typing import Generic, Protocol, TypeVar

T = TypeVar("T")


class Cache(Protocol, Generic[T]):
    """Minimal cache contract required by application services."""

    def get(self, key: str) -> T | None:
        ...

    def set(self, key: str, value: T) -> None:
        ...


__all__ = ["Cache"]
