"""Application boundary for running and inspecting Studio workflows."""

from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from domain.identity import CurrentUser
from domain.studio.runtime import WorkflowExecution


class WorkflowRuntimeService:
    """Coordinates workflow execution use cases without exposing infrastructure to HTTP."""

    def __init__(
        self,
        *,
        workflow_engine: Callable[[], Any],
        workflow_history: Callable[[], Any],
        workflow_queue: Callable[[], Any] | None = None,
        workflows: Callable[[], Any] | None = None,
        datasets: Callable[[], Any] | None = None,
    ) -> None:
        self._workflow_engine = workflow_engine
        self._workflow_history = workflow_history
        self._workflow_queue = workflow_queue
        self._workflows = workflows
        self._datasets = datasets

    def _validate_execution_scope(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        dataset_id: str | None,
    ) -> None:
        if self._workflows is None:
            raise RuntimeError(
                "Workflow repository is required for execution authorization"
            )

        workflow = self._workflows().get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )

        if workflow is None:
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )

        if dataset_id is None:
            return

        if self._datasets is None:
            raise RuntimeError(
                "Dataset repository is required for dataset execution authorization"
            )

        dataset = self._datasets().get_for_owner(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )

        if dataset is None:
            raise ValueError(
                f"Dataset not found: {dataset_id}"
            )

        if dataset.project_id != workflow.project_id:
            raise ValueError(
                f"Dataset does not belong to workflow project: {dataset_id}"
            )

    def execute(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        inputs: dict[str, Any],
        dataset_id: str | None = None,
    ) -> WorkflowExecution:
        self._validate_execution_scope(
            current_user=current_user,
            workflow_id=workflow_id,
            dataset_id=dataset_id,
        )

        return self._workflow_engine().execute(
            workflow_id=workflow_id,
            execution_id=str(uuid4()),
            inputs=inputs,
            dataset_id=dataset_id,
        )

    def execute_async(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        inputs: dict[str, Any],
        dataset_id: str | None = None,
    ) -> WorkflowExecution:
        if self._workflow_queue is None:
            raise RuntimeError(
                "Workflow execution queue is not configured"
            )

        self._validate_execution_scope(
            current_user=current_user,
            workflow_id=workflow_id,
            dataset_id=dataset_id,
        )

        execution_id = str(uuid4())

        queued = self._workflow_engine().create_queued(
            workflow_id=workflow_id,
            execution_id=execution_id,
            inputs=inputs,
            dataset_id=dataset_id,
        )

        self._workflow_queue().dispatch(
            execution_id
        )

        return queued

    def get_execution_detail(self, execution_id: str) -> dict[str, Any]:
        return self._workflow_history().get_workflow_execution_detail(
            execution_id
        )
