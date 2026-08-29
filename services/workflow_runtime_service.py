"""Application boundary for running and inspecting Studio workflows."""

from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from domain.studio.runtime import WorkflowExecution


class WorkflowRuntimeService:
    """Coordinates workflow execution use cases without exposing infrastructure to HTTP."""

    def __init__(
        self,
        *,
        workflow_engine: Callable[[], Any],
        workflow_history: Callable[[], Any],
    ) -> None:
        self._workflow_engine = workflow_engine
        self._workflow_history = workflow_history

    def execute(
        self,
        *,
        workflow_id: str,
        inputs: dict[str, Any],
    ) -> WorkflowExecution:
        return self._workflow_engine().execute(
            workflow_id=workflow_id,
            execution_id=str(uuid4()),
            inputs=inputs,
        )

    def get_execution_detail(self, execution_id: str) -> dict[str, Any]:
        return self._workflow_history().get_workflow_execution_detail(
            execution_id
        )
