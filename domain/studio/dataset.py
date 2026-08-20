"""Dataset domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Dataset:
    """
    Dataset uploaded into an AI Studio project.
    """

    id: str
    project_id: str
    name: str
    source_type: str

    metadata: dict[str, Any]

    created_at: datetime | None = None