"""Materialize transformed tabular data as immutable dataset artifacts."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import BinaryIO
from uuid import uuid4

import pandas as pd

from application.datasets.storage import DatasetStorage


class DatasetArtifactMaterializer:
    """Serialize a DataFrame into a new immutable dataset storage artifact."""

    _SUPPORTED_FORMATS = {"csv", "xlsx"}

    def __init__(self, *, storage: DatasetStorage) -> None:
        self._storage = storage

    def materialize(
        self,
        *,
        frame: pd.DataFrame,
        file_format: str,
        changeset_id: str | None = None,
    ) -> tuple[str, str]:
        extension = file_format.lower().lstrip(".")

        if extension not in self._SUPPORTED_FORMATS:
            raise ValueError(
                "Unsupported dataset artifact format: "
                f"{file_format}"
            )

        artifact_id = changeset_id or uuid4().hex
        storage_key = (
            f"changesets/{artifact_id}/after.{extension}"
        )

        content = self._serialize(
            frame=frame,
            extension=extension,
        )

        content_hash = hashlib.sha256(content).hexdigest()

        self._storage.save(
            storage_key=storage_key,
            content=content,
        )

        with self._storage.open(storage_key=storage_key) as persisted:
            persisted_hash = _hash_stream(persisted)

        if persisted_hash != content_hash:
            raise RuntimeError(
                "Materialized dataset artifact hash verification failed"
            )

        return storage_key, content_hash

    @staticmethod
    def _serialize(
        *,
        frame: pd.DataFrame,
        extension: str,
    ) -> bytes:
        if extension == "csv":
            csv_text = frame.to_csv(
                index=False,
                lineterminator="\n",
            )
            return csv_text.encode("utf-8")

        buffer = BytesIO()

        frame.to_excel(
            buffer,
            index=False,
            engine="openpyxl",
        )

        return buffer.getvalue()


def _hash_stream(source: BinaryIO) -> str:
    hasher = hashlib.sha256()

    while chunk := source.read(1024 * 1024):
        hasher.update(chunk)

    return hasher.hexdigest()


__all__ = ["DatasetArtifactMaterializer"]
