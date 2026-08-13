"""Domain contracts for capability-driven execution plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlanStep:
    """One capability invocation in an execution plan."""

    capability_id: str
    capability_version: str = "1.0"
    parameters: dict[str, Any] = field(default_factory=dict)
    input_mapping: dict[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class ExecutionPlan:
    """Ordered capabilities selected for an execution."""

    steps: tuple[PlanStep, ...]
    version: str = "1.0"
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = ["PlanStep", "ExecutionPlan"]