from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from domain.plans import ExecutionPlan
from domain.workflow_execution_status import WorkflowExecutionStatus


@dataclass(frozen=True)
class WorkflowExecution:
    execution_id: str
    workflow_id: str
    workflow_version: str
    plan: ExecutionPlan
    inputs: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    finished_at: datetime | None = None
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.CREATED
    success: bool = False
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def start(self):
        return replace(
            self,
            status=WorkflowExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

    def pending_approval(self):
        return replace(
            self,
            status=WorkflowExecutionStatus.PENDING_APPROVAL,
        )

    def complete(self, outputs: dict[str, Any]):
        return replace(
            self,
            status=WorkflowExecutionStatus.COMPLETED,
            success=True,
            outputs=outputs,
            finished_at=datetime.now(timezone.utc),
        )

    def cancel(self, error: str | None = None):
        return replace(
            self,
            status=WorkflowExecutionStatus.CANCELLED,
            success=False,
            error=error,
            finished_at=datetime.now(timezone.utc),
        )

    def fail(self, error: str):
        return replace(
            self,
            status=WorkflowExecutionStatus.FAILED,
            success=False,
            error=error,
            finished_at=datetime.now(timezone.utc),
        )
