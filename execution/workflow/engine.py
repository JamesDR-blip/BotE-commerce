"""Runtime engine for AI Studio workflows."""

from __future__ import annotations

from typing import Any
import json
import inspect

from domain.studio.runtime import WorkflowExecution
from domain.workflow_execution_status import WorkflowExecutionStatus

from domain.serialization.execution_plan import (
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

        return self._execute_runtime(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=version.version,
            plan=plan,
            inputs=inputs,
        )

    def create_queued(
        self,
        *,
        workflow_id: str,
        execution_id: str,
        inputs: dict[str, Any],
    ) -> WorkflowExecution:
        """Persist a QUEUED execution using the current active version."""

        workflow = self.workflows.get(
            workflow_id
        )

        if workflow is None:
            raise ValueError(
                f"Workflow not found: {workflow_id}"
            )

        version = self.workflows.get_active_version(
            workflow_id
        )

        if version is None:
            raise ValueError(
                f"No active version for workflow: {workflow_id}"
            )

        if self.executions is None:
            raise RuntimeError(
                "Workflow execution persistence is required for async execution"
            )

        self.executions.create(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=version.version,
            status="QUEUED",
            inputs_json=json.dumps(
                inputs,
                default=str,
            ),
        )

        plan = ExecutionPlanSerializer.from_dict(
            version.plan_json
            if isinstance(version.plan_json, dict)
            else json.loads(version.plan_json)
        )

        return WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=version.version,
            plan=plan,
            inputs=inputs,
            status=WorkflowExecutionStatus.QUEUED,
        )

    def execute_existing(
        self,
        execution_id: str,
    ) -> WorkflowExecution:
        """Execute a previously persisted execution.

        The worker must claim QUEUED -> RUNNING before calling this method.
        The persisted workflow version is used rather than the current active
        version so queued work is deterministic.
        """

        if self.executions is None:
            raise RuntimeError(
                "Workflow execution persistence is required"
            )

        record = self.executions.get(
            execution_id
        )

        if record is None:
            raise ValueError(
                f"Workflow execution not found: {execution_id}"
            )

        if record.status != "RUNNING":
            raise ValueError(
                f"Workflow execution is not running: "
                f"{execution_id} ({record.status})"
            )

        version = self.workflows.get_version(
            record.workflow_id,
            record.workflow_version,
        )

        if version is None:
            raise ValueError(
                "Workflow version not found: "
                f"{record.workflow_id}@{record.workflow_version}"
            )

        inputs = (
            json.loads(record.inputs_json)
            if record.inputs_json
            else {}
        )

        plan = ExecutionPlanSerializer.from_dict(
            version.plan_json
            if isinstance(version.plan_json, dict)
            else json.loads(version.plan_json)
        )

        return self._execute_runtime(
            execution_id=execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            plan=plan,
            inputs=inputs,
        )

    def _execute_runtime(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        plan,
        inputs: dict[str, Any],
    ) -> WorkflowExecution:

        runtime = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
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


class WorkflowExecutionWorker:
    """Claims queued executions and delegates execution to WorkflowEngine."""

    def __init__(
        self,
        *,
        executions,
        workflow_engine: WorkflowEngine,
    ) -> None:
        self._executions = executions
        self._workflow_engine = workflow_engine

    def run(self, execution_id: str) -> None:
        claimed = self._executions.claim_running(
            execution_id
        )

        if claimed is None:
            return

        try:
            self._workflow_engine.execute_existing(
                execution_id
            )
        except Exception as exc:
            self._executions.fail(
                execution_id=execution_id,
                error=str(exc),
            )


