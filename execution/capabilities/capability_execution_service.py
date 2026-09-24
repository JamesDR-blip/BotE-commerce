"""Application service for planning and executing capabilities."""

from __future__ import annotations

from typing import Any, Mapping

from execution.capabilities.capability_executor import CapabilityExecutor
from execution.tracing.trace_collector import ExecutionTraceCollector
from execution.planning.plan_validator import PlanValidator
from infrastructure.observability.telemetry import (
    capability_execution_duration_seconds,
    capability_executions_total,
    tracer,
)

from domain.capability_execution import CapabilityExecutionResult
from domain.plans import ExecutionPlan

class CapabilityExecutionService:
    """Plan and execute capability workflows."""

    def __init__(
        self,
        *,
        executor,
        validator=None,
        lineage_tracking=None,
    ) -> None:
        self._executor = executor
        self._validator = validator or PlanValidator()
        self._lineage_tracking = lineage_tracking


    def execute_plan(
        self,
        *,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        execution_id: str,
        trace_collector=None,
        lineage_context=None,
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

        lineage_callback = None

        if (
            self._lineage_tracking is not None
            and lineage_context is not None
            and lineage_context.get("dataset_id")
            and lineage_context.get("workflow_id")
            and lineage_context.get("workflow_version")
        ):
            def record_lineage(
                *,
                capability_id,
                capability_version,
                inputs,
                outputs,
            ):
                event = self._lineage_tracking.record(
                    dataset_id=lineage_context["dataset_id"],
                    execution_id=execution_id,
                    workflow_id=lineage_context["workflow_id"],
                    workflow_version=lineage_context["workflow_version"],
                    capability_id=capability_id,
                    capability_version=capability_version,
                    event_type="CAPABILITY_EXECUTED",
                    input_refs={
                        "dataset_id": lineage_context["dataset_id"],
                        "input_keys": sorted(inputs.keys()),
                        "previous_event_id": lineage_context.get(
                            "previous_event_id"
                        ),
                    },
                    output_refs={
                        "output_keys": sorted(outputs.keys()),
                    },
                )

                lineage_context["previous_event_id"] = event.id

            lineage_callback = record_lineage

        try:
            with tracer(__name__).start_as_current_span(
                "capability.execute"
            ) as span:
                span.set_attribute(
                    "execution.id",
                    execution_id,
                )
                span.set_attribute(
                    "plan.step_count",
                    len(plan.steps),
                )

                with capability_execution_duration_seconds.time():
                    outputs = self._executor.execute(
                        plan=plan,
                        inputs=inputs,
                        execution_id=execution_id,
                        trace_collector=collector,
                        lineage_callback=lineage_callback,
                    )

            capability_executions_total.labels(
                status="success"
            ).inc()

        except Exception as exc:
            capability_executions_total.labels(
                status="error"
            ).inc()

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
