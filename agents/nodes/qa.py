"""Workflow adapter for validation quality assurance."""
from __future__ import annotations

from typing import Any

from ..qa import QAAgent
from ..state import WorkflowState


class QANode:
    """Adapt workflow state to the QA agent."""

    def __init__(self, agent: QAAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        result = self._agent.result(
            state["fixed_frame"],
            state["issues"],
            state["category"],
            state["rule_version"],
        )

        return {
            "result": result,
        }


__all__ = ["QANode"]