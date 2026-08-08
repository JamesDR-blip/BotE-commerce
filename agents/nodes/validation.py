"""Workflow adapter for deterministic validation."""
from __future__ import annotations

from typing import Any

from plugins.registry import ValidatorRegistry

from ..state import WorkflowState
from ..workflow import ValidatorAgent


class ValidationNode:
    """Resolve the category validator and execute validation."""

    def __init__(
        self,
        agent: ValidatorAgent,
        registry: ValidatorRegistry,
    ) -> None:
        self._agent = agent
        self._registry = registry

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        validator = self._registry.get(state["category"])

        issues = self._agent.validate(
            state["fixed_frame"],
            validator,
            state["rules"],
        )

        return {
            "issues": issues,
        }


__all__ = ["ValidationNode"]