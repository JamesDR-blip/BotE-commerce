"""Service for workflow execution history."""

from __future__ import annotations

import json

class WorkflowHistoryService:

    def __init__(
        self,
        *,
        executions,
        traces,
    ) -> None:

        self.executions = executions
        self.traces = traces

    def get_workflow_execution_detail(
        self,
        execution_id: str,
    ):
        execution = self.executions.get(
            execution_id
        )

        if execution is None:
            raise ValueError(
                f"Workflow execution not found: {execution_id}"
            )

        traces = self.traces.list_by_execution(
            execution_id
        )

        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "workflow_version": execution.workflow_version,
            "status": execution.status,
            "inputs": (
                json.loads(execution.inputs_json)
                if execution.inputs_json
                else {}
            ),
            "outputs": (
                json.loads(execution.outputs_json)
                if execution.outputs_json
                else {}
            ),
            "error": execution.error,
            "created_at": execution.created_at,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "traces": traces,
        }