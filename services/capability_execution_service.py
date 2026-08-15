"""Application service for planning and executing capabilities."""

from __future__ import annotations

from typing import Any, Mapping

from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from services.capability_executor import CapabilityExecutor
from services.execution_trace_collector import ExecutionTraceCollector
from services.plan_validator import PlanValidator


class CapabilityExecutionService:
    """Plan and execute capability workflows."""

    def __init__(
        self,
        planner,
        executor,
        validator=None,
    ):
        self._planner = planner
        self._executor = executor
        self._validator = validator or PlanValidator()

    def execute(
        self,
        requirement: ValidationRequirement,
        inputs: Mapping[str, Any],
        execution_id: str,
        trace_collector=None,
    ) -> dict[str, Any]:

        plan = self._planner.plan(requirement)

        self._validator.validate(
            plan,
            self._executor.registry,
        )

        collector = (
            trace_collector
            or ExecutionTraceCollector(
                execution_id=execution_id
            )
        )

        result = self._executor.execute(
            plan=plan,
            inputs=inputs,
            execution_id=execution_id,
            trace_collector=collector,
        )

        result["_execution_trace"] = collector.trace()

        return result


    def execute_with_trace(
        self,
        requirement: ValidationRequirement,
        inputs: Mapping[str, Any],
        execution_id: str,
    ):
        result = self.execute(
            requirement=requirement,
            inputs=inputs,
            execution_id=execution_id,
        )

        trace = result.pop(
            "_execution_trace"
        )

        return result, trace

__all__ = [
    "CapabilityExecutionService",
]