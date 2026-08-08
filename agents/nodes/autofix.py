"""Workflow adapter for deterministic data autofix."""
from __future__ import annotations

from typing import Any

from plugins.registry import ValidatorRegistry

from ..state import WorkflowState
from ..workflow import AutoFixAgent


class AutoFixNode:
    """Resolve the category validator and apply deterministic autofixes."""

    def __init__(
        self,
        agent: AutoFixAgent,
        registry: ValidatorRegistry,
    ) -> None:
        self._agent = agent
        self._registry = registry

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        validator = self._registry.get(state["category"])

        fixed_frame = self._agent.fix(
            state["frame"],
            validator,
        )

        return {
            "fixed_frame": fixed_frame,
        }


__all__ = ["AutoFixNode"]