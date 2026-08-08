"""Workflow adapter for rule retrieval."""
from __future__ import annotations

from typing import Any

from ..rule_retriever import RuleRetrieverAgent
from ..state import WorkflowState


class RuleRetrievalNode:
    """Adapt workflow state to the rule retrieval agent."""

    def __init__(self, agent: RuleRetrieverAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        category = state["category"]

        rules, version = self._agent.retrieve(category)

        return {
            "rules": rules,
            "rule_version": version,
        }


__all__ = ["RuleRetrievalNode"]