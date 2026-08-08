"""Workflow adapter for requirement interpretation."""
from __future__ import annotations

from typing import Any

from ..requirement import RequirementAgent
from ..state import WorkflowState


class RequirementNode:
    """Adapt WorkflowState to RequirementAgent without coupling the agent to LangGraph."""

    def __init__(self, agent: RequirementAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        requirement = self._agent.interpret(
            state.get("requested_category")
        )
        return {"requirement": requirement}


__all__ = ["RequirementNode"]