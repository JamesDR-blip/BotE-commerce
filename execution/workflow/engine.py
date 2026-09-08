"""Runtime engine for AI Studio workflows."""

from __future__ import annotations

from typing import Any
import json
import inspect

from domain.studio.runtime import WorkflowExecution

from infrastructure.serialization.execution_plan import (
    ExecutionPlanSerializer,
)
from execution.tracing.trace_collector import (
    ExecutionTraceCollector,
)

class WorkflowEngine:

    def __init__(
        self,
        *,
        workflows,
        capability_execution,
        executions=None,
        trace_persistence=None,
    ) -> None:

        self.workflows = workflows
        self.capability_execution = capability_execution
        self.executions = executions
        self.trace_persistence = trace_persistence


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
                inputs_json=json.dumps(
                    inputs,
                    default=str,
                ),
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

        trace_collector = ExecutionTraceCollector(
            execution_id=execution_id
        )

        if self.capability_execution is None:
            return runtime

        try:
            execute_plan = (
                self.capability_execution.execute_plan
            )

            parameters = inspect.signature(
                execute_plan
            ).parameters

            if "trace_collector" in parameters:
                result = execute_plan(
                    plan=plan,
                    inputs=inputs,
                    execution_id=execution_id,
                    trace_collector=trace_collector,
                )
            else:
                result = execute_plan(
                    plan=plan,
                    inputs=inputs,
                    execution_id=execution_id,
                )

            trace = getattr(
                result,
                "trace",
                None,
            )

            if trace is None:
                trace = trace_collector.trace()

            if (
                self.trace_persistence is not None
                and trace is not None
            ):
                self.trace_persistence.save(trace)

        except Exception as exc:
            trace = getattr(
                exc,
                "execution_trace",
                None,
            )

            if trace is None:
                trace = trace_collector.trace()

            if (
                self.trace_persistence is not None
                and trace.records
            ):
                self.trace_persistence.save(trace)

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
                    completed.outputs,
                    default=str,
                ),
            )

        return completed
    
