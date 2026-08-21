"""Service for workflow execution history."""

from __future__ import annotations


class WorkflowHistoryService:

    def __init__(
        self,
        *,
        executions,
        traces,
    ) -> None:

        self.executions = executions
        self.traces = traces


    def get_execution(
        self,
        execution_id: str,
    ):

        execution = self.executions.get(
            execution_id
        )

        if execution is None:
            raise ValueError(
                f"Execution not found: {execution_id}"
            )

        trace_records = (
            self.traces.list_by_execution(
                execution_id
            )
        )

        return {
            "execution": execution,
            "traces": trace_records,
        }

    def get_execution_history(
        self,
        execution_id: str,
    ):
        return self.get_execution(
            execution_id
        )
    
    def get_execution_detail(
        self,
        execution_id: str,
    ):
        data = self.get_execution(
            execution_id
        )

        execution = data["execution"]

        return {
            "execution_id": execution.id,
            "category": execution.category,
            "status": execution.status,
            "health_score": execution.health_score,
            "created_at": execution.created_at,
            "requirement_json": execution.requirement_json,
            "plan_json": execution.plan_json,
            "planner_version": execution.planner_version,
            "traces": data["traces"],
        }