"""Thread-safe TTL cache for idempotent source/rules validations."""
from __future__ import annotations
from threading import Lock
from time import monotonic
from typing import TypeVar
T = TypeVar("T")

class TTLCache:
    def __init__(self, ttl_seconds: int) -> None: self._ttl, self._data, self._lock = ttl_seconds, {}, Lock()
    def get(self, key: str) -> T | None:
        with self._lock:
            item = self._data.get(key)
            if not item or item[0] < monotonic(): self._data.pop(key, None); return None
            return item[1]
    def set(self, key: str, value: T) -> None:
        with self._lock: self._data[key] = (monotonic() + self._ttl, value)
