"""Domain contract for capability execution results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from domain.execution_trace import ExecutionTrace
from domain.plans import ExecutionPlan


@dataclass(frozen=True)
class CapabilityExecutionResult:
    """Complete result of executing an execution plan."""

    outputs: Mapping[str, Any]

    plan: ExecutionPlan

    trace: ExecutionTrace

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


__all__ = [
    "CapabilityExecutionResult",
]