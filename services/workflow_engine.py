"""Runtime engine for AI Studio workflows."""

from __future__ import annotations

from typing import Any
import json

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
        executions=None,
    ) -> None:

        self.workflows = workflows
        self.capability_execution = capability_execution
        self.executions = executions


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
                else json.loads(
                    version.plan_json
                )
            )
        )

        if self.executions is not None:
            self.executions.create(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_version=version.version,
                inputs_json=json.dumps(inputs),
            )

            self.executions.mark_running(
                execution_id
            )


        runtime = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=version.version,
            plan=plan,
            inputs=inputs,
        )


        runtime = runtime.start()


        if self.capability_execution is None:
            return runtime


        try:
            result = self.capability_execution.execute_plan(
                plan=plan,
                inputs=inputs,
                execution_id=execution_id,
            )

        except Exception as exc:

            failed = runtime.fail(
                error=str(exc)
            )

            if self.executions is not None:
                self.executions.fail(
                    execution_id=execution_id,
                    error=str(exc),
                )

            return failed


        completed = runtime.complete(
            outputs=dict(result.outputs)
        )

        if self.executions is not None:
            self.executions.complete(
                execution_id=execution_id,
                outputs_json=json.dumps(
                    completed.outputs
                ),
            )

        return completed
    