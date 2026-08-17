"""Application-level execution context."""

from __future__ import annotations

from dataclasses import dataclass

from agents.requirement import ValidationRequirement
from domain.plans import ExecutionPlan


@dataclass(frozen=True)
class ExecutionContext:
    """Persisted inputs required to understand or replay an execution."""

    requirement: ValidationRequirement
    plan: ExecutionPlan
    planner_version: str | None