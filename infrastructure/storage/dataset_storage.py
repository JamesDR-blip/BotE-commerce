"""Persistent storage for uploaded dataset sources."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import BinaryIO


class DatasetStorage:
    """Store and reopen dataset source files through a safe storage boundary."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, *, storage_key: str, content: bytes) -> str:
        target = self._safe_path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_key

    def save_stream(
        self,
        *,
        storage_key: str,
        source: BinaryIO,
    ) -> str:
        target = self._safe_path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)

        return storage_key

    def open(self, *, storage_key: str) -> BinaryIO:
        target = self._safe_path(storage_key)
        if not target.is_file():
            raise FileNotFoundError(
                f"Dataset source not found: {storage_key}"
            )
        return target.open("rb")

    def _safe_path(self, storage_key: str) -> Path:
        if not storage_key:
            raise ValueError("storage_key must not be empty")

        normalized = PurePosixPath(storage_key)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("Invalid dataset storage key")

        target = (self._root / Path(*normalized.parts)).resolve()

        try:
            target.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("Invalid dataset storage key") from exc

        return target


__all__ = ["DatasetStorage"]
