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
        data_health: Callable[[], Any] | None = None,
        risk_service: Callable[[], Any] | None = None,
        risk_assessments: Callable[[], Any] | None = None,
        workflow_executions: Callable[[], Any] | None = None,
    ) -> None:
        self._workflow_engine = workflow_engine
        self._workflow_history = workflow_history
        self._workflow_queue = workflow_queue
        self._workflows = workflows
        self._datasets = datasets
        self._data_health = data_health
        self._risk_service = risk_service
        self._risk_assessments = risk_assessments
        self._workflow_executions = workflow_executions

    def _validate_execution_scope(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        dataset_id: str | None,
    ) -> None:
        if self._workflows is None:
            return

        workflow = self._workflows().get_for_owner(
            workflow_id=workflow_id,
            owner_id=current_user.user_id,
        )

        if workflow is None:
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )

        if dataset_id is None or self._datasets is None:
            return

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

    def _risk_gate_enabled(self) -> bool:
        return (
            self._risk_service is not None
            and self._risk_assessments is not None
            and self._workflow_executions is not None
        )

    @staticmethod
    def _blast_radius(plan: Any) -> float:
        metadata = getattr(plan, "metadata", {}) or {}
        risk = metadata.get("risk", {})

        if not isinstance(risk, dict):
            return 0.0

        value = risk.get("blast_radius", 0.0)

        if isinstance(value, bool):
            raise ValueError(
                "risk.blast_radius must be between 0 and 1"
            )

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "risk.blast_radius must be between 0 and 1"
            ) from exc

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "risk.blast_radius must be between 0 and 1"
            )

        return value

    def _confidence(
        self,
        *,
        current_user: CurrentUser,
        dataset_id: str | None,
    ) -> float:
        if (
            dataset_id is None
            or self._data_health is None
        ):
            return 1.0

        health = self._data_health().get_health(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )

        value = float(health.confidence_score)

        # DataHealthScore is a normalized 0..1 confidence value.
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "data health confidence must be between 0 and 1"
            )

        return value

    def _assess_execution(
        self,
        *,
        execution_id: str,
        plan: Any,
        current_user: CurrentUser,
        dataset_id: str | None,
    ):
        if not self._risk_gate_enabled():
            return None

        result = self._risk_service().evaluate(
            blast_radius=self._blast_radius(plan),
            confidence=self._confidence(
                current_user=current_user,
                dataset_id=dataset_id,
            ),
        )

        self._risk_assessments().create(
            assessment_id=str(uuid4()),
            execution_id=execution_id,
            risk_score=result.risk_score.value,
            confidence_score=result.confidence.value,
            approval_required=result.approval_required,
        )

        return result

    def _pending_execution(
        self,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        self._workflow_executions().mark_pending_approval(
            execution.execution_id
        )
        return execution.pending_approval()

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

        engine = self._workflow_engine()

        # Preserve legacy fake/test engines that only implement execute().
        if (
            not self._risk_gate_enabled()
            or not hasattr(engine, "create_queued")
            or not hasattr(engine, "execute_existing")
        ):
            return engine.execute(
                workflow_id=workflow_id,
                execution_id=str(uuid4()),
                inputs=inputs,
                dataset_id=dataset_id,
            )

        execution = engine.create_queued(
            workflow_id=workflow_id,
            execution_id=str(uuid4()),
            inputs=inputs,
            dataset_id=dataset_id,
        )

        result = self._assess_execution(
            execution_id=execution.execution_id,
            plan=execution.plan,
            current_user=current_user,
            dataset_id=dataset_id,
        )

        if result is not None and result.approval_required:
            return self._pending_execution(execution)

        self._workflow_executions().mark_running(
            execution.execution_id
        )

        return engine.execute_existing(
            execution.execution_id
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
                "Workflow queue is required for async execution"
            )

        self._validate_execution_scope(
            current_user=current_user,
            workflow_id=workflow_id,
            dataset_id=dataset_id,
        )

        engine = self._workflow_engine()

        execution = engine.create_queued(
            workflow_id=workflow_id,
            execution_id=str(uuid4()),
            inputs=inputs,
            dataset_id=dataset_id,
        )

        if not self._risk_gate_enabled():
            self._workflow_queue().dispatch(
                execution.execution_id
            )
            return execution

        result = self._assess_execution(
            execution_id=execution.execution_id,
            plan=execution.plan,
            current_user=current_user,
            dataset_id=dataset_id,
        )

        if result is not None and result.approval_required:
            return self._pending_execution(execution)

        self._workflow_queue().dispatch(
            execution.execution_id
        )

        return execution

    def get_execution_detail(
        self,
        execution_id: str,
    ) -> Any:
        return self._workflow_history().get_workflow_execution_detail(
            execution_id
        )
