"""Dataset ingestion service."""

from __future__ import annotations

import hashlib
from pathlib import PurePath
from typing import Any, BinaryIO, Protocol

import pandas as pd

from domain.studio.profiling import DatasetProfileService
from application.datasets.storage import DatasetStorage


class TabularReader(Protocol):
    def read(self, filename: str | None, content: bytes) -> pd.DataFrame:
        ...


class StreamingTabularReader(Protocol):
    def stream(self, filename: str | None, source: BinaryIO):
        ...


class _HashingReader:
    """Read a binary stream while tracking its size and SHA-256 hash."""

    def __init__(self, source: BinaryIO) -> None:
        self._source = source
        self._hasher = hashlib.sha256()
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    @property
    def content_hash(self) -> str:
        return self._hasher.hexdigest()

    def read(self, size: int = -1) -> bytes:
        chunk = self._source.read(size)

        if chunk:
            self._hasher.update(chunk)
            self._size += len(chunk)

        return chunk

    @property
    def content_hash(self) -> str:
        return self._hasher.hexdigest()

class DatasetIngestionService:
    """Ingest uploaded tabular files into persistent Dataset records."""

    def __init__(
        self,
        *,
        reader: TabularReader,
        streaming_reader: StreamingTabularReader,
        datasets: Any,
        profiler: DatasetProfileService,
        storage: DatasetStorage | None = None,
    ) -> None:
        self.reader = reader
        self.streaming_reader = streaming_reader
        self.datasets = datasets
        self.profiler = profiler
        self.storage = storage

    def ingest(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        filename: str,
        content: bytes,
        source_type: str = "upload",
    ):
        frame = self.reader.read(filename, content)

        profile = self.profiler.profile(frame)

        storage_key = None
        if self.storage is not None:
            suffix = PurePath(filename).suffix.lower()
            storage_key = f"{dataset_id}{suffix}"
            self.storage.save(
                storage_key=storage_key,
                content=content,
            )

        extension = PurePath(filename).suffix.lower().lstrip(".")

        return self.datasets.create(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            source_type=source_type,
            metadata={
                "profile": {
                    "row_count": profile.row_count,
                    "column_count": profile.column_count,
                    "duplicate_row_count": profile.duplicate_row_count,
                    "columns": [
                        {
                            "name": column.name,
                            "dtype": column.dtype,
                            "null_count": column.null_count,
                            "null_ratio": column.null_ratio,
                            "unique_count": column.unique_count,
                            "sample_values": list(column.sample_values),
                        }
                        for column in profile.columns
                    ],
                }
            },
            filename=filename,
            file_format=extension,
            size_bytes=len(content),
            content_hash=hashlib.sha256(content).hexdigest(),
            storage_key=storage_key,
            row_count=len(frame),
            column_count=len(frame.columns),
            status="READY",
        )

    def ingest_streaming(
        self,
        *,
        dataset_id: str,
        project_id: str,
        name: str,
        filename: str,
        source: BinaryIO,
        storage_key: str | None = None,
        source_type: str = "upload",
    ):
        """Persist and profile CSV/XLSX while processing one chunk at a time."""
        from application.datasets.streaming_profiling import (
            StreamingProfileAccumulator,
        )

        if self.storage is None:
            raise RuntimeError(
                "Dataset storage is required for streaming ingestion"
            )

        if storage_key is None:
            suffix = PurePath(filename).suffix.lower()
            storage_key = f"{dataset_id}{suffix}"

        hashing_source = _HashingReader(source)

        self.storage.save_stream(
            storage_key=storage_key,
            source=hashing_source,
        )

        size_bytes = hashing_source.size
        content_hash = hashing_source.content_hash

        with self.storage.open(storage_key=storage_key) as persisted_source:
            accumulator = StreamingProfileAccumulator()

            for chunk in self.streaming_reader.stream(
                filename,
                persisted_source,
            ):
                accumulator.update(chunk)

        profile = accumulator.finalize()
        extension = PurePath(filename).suffix.lower().lstrip(".")

        return self.datasets.create(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            source_type=source_type,
            metadata={
                "profile": {
                    "row_count": profile.row_count,
                    "column_count": profile.column_count,
                    "duplicate_row_count": profile.duplicate_row_count,
                    "columns": [
                        {
                            "name": column.name,
                            "dtype": column.dtype,
                            "null_count": column.null_count,
                            "null_ratio": column.null_ratio,
                            "unique_count": column.unique_count,
                            "sample_values": list(column.sample_values),
                        }
                        for column in profile.columns
                    ],
                }
            },
            filename=filename,
            file_format=extension,
            size_bytes=size_bytes,
            content_hash=content_hash,
            storage_key=storage_key,
            row_count=profile.row_count,
            column_count=profile.column_count,
            status="READY",
        )

