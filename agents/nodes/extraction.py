"""Workflow adapter for deterministic product extraction."""
from __future__ import annotations

from typing import Any

from ..extraction import ExtractionAgent
from ..state import WorkflowState


class ExtractionNode:
    """Adapt workflow state to the extraction agent."""

    def __init__(self, agent: ExtractionAgent) -> None:
        self._agent = agent

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        extractions = self._agent.extract(state["frame"])

        return {
            "extractions": extractions,
        }


__all__ = ["ExtractionNode"]