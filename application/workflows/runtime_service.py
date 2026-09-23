"""Application boundary for running and inspecting Studio workflows."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from application.approval.approval_service import ApprovalService
from domain.approval import ApprovalRequest
from domain.identity import CurrentUser
from domain.studio.runtime import WorkflowExecution
from domain.quota import QuotaDimension
from services.authorization import AuthorizationService
from services.compliance import ComplianceService
from services.quota import QuotaService


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
        projects: Callable[[], Any] | None = None,
        workspaces: Callable[[], Any] | None = None,
        authorization: AuthorizationService | None = None,
        data_health: Callable[[], Any] | None = None,
        risk_service: Callable[[], Any] | None = None,
        risk_assessments: Callable[[], Any] | None = None,
        workflow_executions: Callable[[], Any] | None = None,
        changeset_service: Callable[[], Any] | None = None,
        approval_service: Callable[[], ApprovalService] | None = None,
        quota_service: Callable[[], QuotaService] | None = None,
        compliance_service: Callable[[], ComplianceService] | None = None,
    ) -> None:
        self._workflow_engine = workflow_engine
        self._workflow_history = workflow_history
        self._workflow_queue = workflow_queue
        self._workflows = workflows
        self._datasets = datasets
        self._projects = projects
        self._workspaces = workspaces
        self._authorization = authorization
        self._data_health = data_health
        self._risk_service = risk_service
        self._risk_assessments = risk_assessments
        self._workflow_executions = workflow_executions
        self._changeset_service = changeset_service
        self._approval_service = approval_service
        self._quota_service = quota_service
        self._compliance_service = compliance_service

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

    def _organization_id_for_workflow(
        self,
        *,
        workflow,
        owner_id: str,
    ) -> str | None:
        if self._authorization is None:
            return None

        if self._projects is None or self._workspaces is None:
            raise RuntimeError(
                "Project and workspace repositories are required "
                "for workflow authorization"
            )

        project = self._projects().get_for_owner(
            project_id=workflow.project_id,
            owner_id=owner_id,
        )
        if project is None:
            raise ValueError(
                f"Project not found: {workflow.project_id}"
            )

        workspace = self._workspaces().get_for_owner(
            workspace_id=project.workspace_id,
            owner_id=owner_id,
        )
        if workspace is None:
            raise ValueError(
                f"Workspace not found: {project.workspace_id}"
            )

        return workspace.organization_id

    def _authorize_execution(
        self,
        *,
        current_user: CurrentUser,
        organization_id: str | None,
    ) -> None:
        if self._authorization is None or organization_id is None:
            return

        self._authorization.authorize(
            user=current_user,
            resource="workflow",
            action="execute",
            organization_id=organization_id,
        )

    def _check_execution_compliance(
        self,
        *,
        organization_id: str | None,
        workflow_id: str,
        dataset_id: str | None,
    ) -> None:
        if self._compliance_service is None or organization_id is None:
            return

        context = {
            "workflow_id": workflow_id,
        }

        if dataset_id is not None:
            context["dataset_id"] = dataset_id

        self._compliance_service().check(
            organization_id=organization_id,
            resource="workflow",
            action="execute",
            context=context,
        )

    def _check_execution_quota(
        self,
        *,
        organization_id: str | None,
    ) -> None:
        if self._quota_service is None:
            return

        self._quota_service().check(
            organization_id=organization_id,
            dimension=QuotaDimension.WORKFLOW_EXECUTION_COUNT,
            requested_usage=1,
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

    def _prepare_candidate(
        self,
        *,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        if self._changeset_service is None:
            raise RuntimeError(
                "ChangeSet service is required before entering "
                "PENDING_APPROVAL"
            )

        changeset = self._changeset_service().prepare_candidate(
            execution_id=execution.execution_id,
        )

        return replace(
            execution,
            changeset_id=changeset.id,
        )

    def _request_approval(
        self,
        *,
        execution: WorkflowExecution,
        risk_score: Any,
        confidence_score: float,
        current_user: CurrentUser,
    ) -> None:
        if self._approval_service is None:
            raise RuntimeError(
                "Approval service is required before entering "
                "PENDING_APPROVAL"
            )

        if execution.changeset_id is None:
            raise RuntimeError(
                "ChangeSet is required before requesting approval"
            )

        request = ApprovalRequest(
            approval_id=str(uuid4()),
            execution_id=execution.execution_id,
            changeset_id=execution.changeset_id,
            risk_score=str(getattr(risk_score, "value", risk_score)),
            confidence_score=confidence_score,
            requested_by=current_user.user_id,
            created_at=datetime.now(timezone.utc),
        )

        self._approval_service().request_approval(request)

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

        organization_id = None
        if self._authorization is not None:
            workflow = self._workflows().get_for_owner(
                workflow_id=workflow_id,
                owner_id=current_user.user_id,
            )
            if workflow is None:
                raise ValueError(
                    f"Workflow not found: {workflow_id}"
                )

            organization_id = self._organization_id_for_workflow(
                workflow=workflow,
                owner_id=current_user.user_id,
            )

        self._authorize_execution(
            current_user=current_user,
            organization_id=organization_id,
        )
        self._check_execution_compliance(
            organization_id=organization_id,
            workflow_id=workflow_id,
            dataset_id=dataset_id,
        )
        self._check_execution_quota(
            organization_id=organization_id,
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
            execution = self._prepare_candidate(
                execution=execution,
            )
            self._request_approval(
                execution=execution,
                risk_score=result.risk_score,
                confidence_score=result.confidence.value,
                current_user=current_user,
            )
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

        organization_id = None
        if self._authorization is not None:
            workflow = self._workflows().get_for_owner(
                workflow_id=workflow_id,
                owner_id=current_user.user_id,
            )
            if workflow is None:
                raise ValueError(
                    f"Workflow not found: {workflow_id}"
                )

            organization_id = self._organization_id_for_workflow(
                workflow=workflow,
                owner_id=current_user.user_id,
            )

        self._authorize_execution(
            current_user=current_user,
            organization_id=organization_id,
        )
        self._check_execution_compliance(
            organization_id=organization_id,
            workflow_id=workflow_id,
            dataset_id=dataset_id,
        )
        self._check_execution_quota(
            organization_id=organization_id,
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
            execution = self._prepare_candidate(
                execution=execution,
            )
            self._request_approval(
                execution=execution,
                risk_score=result.risk_score,
                confidence_score=result.confidence.value,
                current_user=current_user,
            )
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

