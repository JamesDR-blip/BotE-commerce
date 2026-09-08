"""Application service for loading persisted execution context."""

from __future__ import annotations

import json

from domain.execution_context import ExecutionContext
from services.execution_plan_serializer import ExecutionPlanSerializer
from services.requirement_serializer import RequirementSerializer


class ExecutionContextService:
    """Load and reconstruct persisted execution context."""

    def __init__(self, executions) -> None:
        self._executions = executions

    def get(
        self,
        execution_id: str,
    ) -> ExecutionContext | None:
        data = self._executions.execution_context(
            execution_id
        )

        if data is None:
            return None

        requirement_json = data["requirement_json"]
        plan_json = data["plan_json"]

        if requirement_json is None:
            raise ValueError(
                f"Execution {execution_id} has no persisted requirement"
            )

        if plan_json is None:
            raise ValueError(
                f"Execution {execution_id} has no persisted plan"
            )

        requirement = RequirementSerializer.from_dict(
            json.loads(requirement_json)
        )

        plan = ExecutionPlanSerializer.from_dict(
            json.loads(plan_json)
        )

        return ExecutionContext(
            requirement=requirement,
            plan=plan,
            planner_version=data["planner_version"],
        )
