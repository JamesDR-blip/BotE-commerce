"""Domain contract for persisted execution context."""

from __future__ import annotations

from dataclasses import dataclass

from agents.requirement import ValidationRequirement
from domain.plans import ExecutionPlan


@dataclass(frozen=True)
class ExecutionContext:
    requirement: ValidationRequirement
    plan: ExecutionPlan
    planner_version: str | None