"""Application service for planning and executing capabilities."""

from __future__ import annotations

from typing import Any, Mapping

from execution.capabilities.capability_executor import CapabilityExecutor
from execution.tracing.trace_collector import ExecutionTraceCollector
from execution.planning.plan_validator import PlanValidator

from domain.capability_execution import CapabilityExecutionResult
from domain.plans import ExecutionPlan

class CapabilityExecutionService:
    """Plan and execute capability workflows."""

    def __init__(
        self,
        *,
        executor,
        validator=None,
    ) -> None:
        self._executor = executor
        self._validator = validator or PlanValidator()


    def execute_plan(
        self,
        *,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        execution_id: str,
        trace_collector=None,
    ) -> CapabilityExecutionResult:

        self._validator.validate(
            plan,
            self._executor.registry,
            external_inputs=inputs.keys(),
        )

        collector = (
            trace_collector
            or ExecutionTraceCollector(
                execution_id=execution_id
            )
        )

        try:
            outputs = self._executor.execute(
                plan=plan,
                inputs=inputs,
                execution_id=execution_id,
                trace_collector=collector,
            )

        except Exception as exc:
            trace = collector.trace()

            if trace.records:
                # Expose partial trace to the caller
                setattr(
                    exc,
                    "execution_trace",
                    trace,
                )

            raise

        return CapabilityExecutionResult(
            outputs=outputs,
            plan=plan,
            trace=collector.trace(),
        )

__all__ = [
    "CapabilityExecutionService",
]
