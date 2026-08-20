"""Runtime engine for AI Studio workflows."""

from __future__ import annotations

from typing import Any

from domain.studio.runtime import WorkflowExecution

from services.execution_plan_serializer import (
    ExecutionPlanSerializer,
)


class WorkflowEngine:

    def __init__(
        self,
        *,
        workflows,
        capability_execution,
    ) -> None:

        self.workflows = workflows
        self.capability_execution = capability_execution


    def execute(
        self,
        *,
        workflow_id: str,
        execution_id: str,
        inputs: dict[str, Any],
    ) -> WorkflowExecution:


        workflow = self.workflows.get(
            workflow_id
        )

        if workflow is None:
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )


        version = (
            self.workflows
            .get_active_version(
                workflow_id
            )
        )


        if version is None:
            raise ValueError(
                f"No active version for workflow: {workflow_id}"
            )


        plan = (
            ExecutionPlanSerializer
            .from_dict(
                version.plan_json
                if isinstance(
                    version.plan_json,
                    dict,
                )
                else __import__(
                    "json"
                ).loads(
                    version.plan_json
                )
            )
        )


        runtime = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=version.version,
            plan=plan,
            inputs=inputs,
        )


        return runtime