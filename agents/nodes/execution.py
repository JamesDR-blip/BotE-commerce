"""Workflow execution lifecycle adapters."""
from __future__ import annotations

from typing import Any

from ..state import WorkflowState


class ExecutionStartNode:
    """Initialize execution lifecycle state."""

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "execution_status": "RUNNING",
            "workflow": state.get("workflow", "validation"),
        }


class ExecutionCompleteNode:
    """Mark a successfully completed workflow."""

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "execution_status": "COMPLETED",
        }


class ExecutionFailedNode:
    """Mark a failed workflow execution."""

    def __call__(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "execution_status": "FAILED",
        }

__all__ = [
    "ExecutionStartNode",
    "ExecutionCompleteNode",
    "ExecutionFailedNode",
]