"""Application contract for persistent dataset source storage."""

from __future__ import annotations

from typing import BinaryIO, Protocol


class DatasetStorage(Protocol):
    """Persist and reopen dataset source bytes."""

    def save(self, *, storage_key: str, content: bytes) -> str:
        ...

    def save_stream(
        self,
        *,
        storage_key: str,
        source: BinaryIO,
    ) -> str:
        ...

    def open(self, *, storage_key: str) -> BinaryIO:
        ...
