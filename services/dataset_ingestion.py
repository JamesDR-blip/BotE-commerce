"""Dataset ingestion service."""

from __future__ import annotations

import hashlib
from pathlib import PurePath
from typing import Any

from services.upload_reader import TabularUploadReader
from domain.studio.profiling import DatasetProfileService


class DatasetIngestionService:
    """Ingest uploaded tabular files into persistent Dataset records."""

    def __init__(
        self,
        *,
        reader: TabularUploadReader,
        datasets: Any,
        profiler: DatasetProfileService,
    ) -> None:
        self.reader = reader
        self.datasets = datasets
        self.profiler = profiler

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
            row_count=len(frame),
            column_count=len(frame.columns),
            status="READY",
        )
