"""Application port for asynchronous workflow dispatch."""

from __future__ import annotations

from typing import Protocol


class WorkflowExecutionQueue(Protocol):
    """Dispatches persisted workflow execution IDs for background processing."""

    def dispatch(self, execution_id: str) -> None:
        ...
