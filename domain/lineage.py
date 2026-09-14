"""Domain contract for immutable data lineage events."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DataLineageEvent:
    id: str
    dataset_id: str
    execution_id: str
    workflow_id: str
    workflow_version: str
    capability_id: str
    capability_version: str
    event_type: str
    input_refs: dict[str, Any] = field(default_factory=dict)
    output_refs: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
