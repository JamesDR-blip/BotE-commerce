"""Deterministic planner for the validation orchestration graph."""
from __future__ import annotations

from .state import WorkflowState


class PlannerAgent:
    """Select the standard validation steps without performing their work."""

    _VALIDATION_PLAN = ("classify", "retrieve_rules", "autofix", "validate", "qa")

    def plan(self, state: WorkflowState) -> dict[str, tuple[str, ...]]:
        if not state["categories"]:
            raise ValueError("No validator categories are registered")
        return {"plan": self._VALIDATION_PLAN}
