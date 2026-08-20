"""Workflow domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.plans import ExecutionPlan


@dataclass(frozen=True)
class Workflow:
    """
    Persisted AI workflow definition.

    A workflow stores a generated execution plan.
    """

    id: str

    project_id: str

    name: str

    version: str

    plan: ExecutionPlan

    created_at: datetime | None = None