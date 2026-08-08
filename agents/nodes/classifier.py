"""Workflow adapter for category classification."""
from __future__ import annotations

from typing import Any

from ..category import CategoryAgent
from ..state import WorkflowState


class ClassifierNode:
    """Adapt workflow state to the category classification agent."""

    def __init__(self, agent: CategoryAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        requirement = state["requirement"]

        category = self._agent.classify(
            state["frame"],
            state["categories"],
            requirement.requested_category,
        )

        return {"category": category}


__all__ = ["ClassifierNode"]