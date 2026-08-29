"""Dataset domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Dataset:
    """Dataset managed by an AI Studio project."""

    id: str
    project_id: str
    name: str
    source_type: str

    metadata: dict[str, Any]

    filename: str | None = None
    file_format: str | None = None
    size_bytes: int | None = None
    content_hash: str | None = None

    row_count: int | None = None
    column_count: int | None = None

    status: str = "READY"

    created_at: datetime | None = None