"""Workflow adapter for capability-driven planning."""
from __future__ import annotations

from typing import Any

from ..planner import PlannerAgent
from ..state import WorkflowState


class PlannerNode:
    """Adapt WorkflowState to PlannerAgent without coupling the agent to LangGraph."""

    def __init__(self, agent: PlannerAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        requirement = state["requirement"]

        execution_plan = self._agent.plan(requirement)

        return {
            "execution_plan": execution_plan,
        }


__all__ = ["PlannerNode"]