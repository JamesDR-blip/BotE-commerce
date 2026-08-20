"""Runtime contracts for Studio workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domain.plans import ExecutionPlan


@dataclass(frozen=True)
class WorkflowExecution:
    """
    A single workflow execution instance.
    """

    execution_id: str

    workflow_id: str

    workflow_version: str

    plan: ExecutionPlan

    inputs: dict[str, Any] = field(
        default_factory=dict
    )

    started_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )

    finished_at: datetime | None = None

    success: bool = False

    outputs: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None