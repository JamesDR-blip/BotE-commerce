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
from infrastructure.observability.telemetry import (
    record_workflow_state_transition,
    tracer,
    workflow_execution_duration_seconds,
    workflow_executions_total,
)

class WorkflowEngine:

    def __init__(
        self,
        *,
        workflows,
        capability_execution,
        executions=None,
        trace_persistence=None,
        datasets=None,
        streaming_reader=None,
        dataset_storage=None,
    ) -> None:

        self.workflows = workflows
        self.capability_execution = capability_execution
        self.executions = executions
        self.trace_persistence = trace_persistence
        self.datasets = datasets
        self.streaming_reader = streaming_reader
        self.dataset_storage = dataset_storage

    def execute(
        self,
        *,
        workflow_id: str,
        execution_id: str,
        inputs: dict[str, Any],
        dataset_id: str | None = None,
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

        execution_metadata = plan.metadata.get("execution", {})
        streaming = execution_metadata.get("mode") == "streaming"

        if streaming and dataset_id is None:
            raise ValueError(
                "Streaming workflow execution requires a dataset_id"
            )

        if self.executions is not None:
            self.executions.create(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_version=version.version,
                dataset_id=dataset_id,
                inputs_json=json.dumps(
                    inputs,
                    default=str,
                ),
            )

            self.executions.mark_running(
                execution_id
            )

        record_workflow_state_transition(
            workflow_id=workflow_id,
            execution_id=execution_id,
            from_state="CREATED",
            to_state="RUNNING",
        )

        if streaming:
            return self._execute_streaming_runtime(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_version=version.version,
                plan=plan,
                inputs=inputs,
                dataset_id=dataset_id,
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
        dataset_id: str | None = None,
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
            dataset_id=dataset_id,
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

        execution_metadata = plan.metadata.get("execution", {})
        if execution_metadata.get("mode") == "streaming":
            if record.dataset_id is None:
                raise ValueError(
                    "Streaming workflow execution requires a dataset_id"
                )

            return self._execute_streaming_runtime(
                execution_id=execution_id,
                workflow_id=record.workflow_id,
                workflow_version=record.workflow_version,
                plan=plan,
                inputs=inputs,
                dataset_id=record.dataset_id,
            )

        return self._execute_runtime(
            execution_id=execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            plan=plan,
            inputs=inputs,
        )

    def _execute_streaming_runtime(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        plan,
        inputs: dict[str, Any],
        dataset_id: str,
    ) -> WorkflowExecution:
        lineage_context = {
            "dataset_id": dataset_id,
            "workflow_id": workflow_id,
            "workflow_version": workflow_version,
        }

        runtime = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            plan=plan,
            inputs=inputs,
        ).start()

        if self.datasets is None:
            raise RuntimeError(
                "Dataset repository is required for streaming execution"
            )

        dataset = self.datasets.get(dataset_id)

        if dataset is None:
            raise ValueError(
                f"Dataset not found: {dataset_id}"
            )

        if not dataset.storage_key:
            raise ValueError(
                f"Dataset has no persisted storage: {dataset_id}"
            )

        if self.dataset_storage is None:
            raise RuntimeError(
                "Dataset storage is required for streaming execution"
            )

        if self.streaming_reader is None:
            raise RuntimeError(
                "Streaming reader is required for streaming execution"
            )

        processed_chunks = 0
        processed_rows = 0

        try:
            with tracer(__name__).start_as_current_span(
                "workflow.execute"
            ) as span:
                span.set_attribute(
                    "execution.id",
                    execution_id,
                )
                span.set_attribute(
                    "workflow.id",
                    workflow_id,
                )
                span.set_attribute(
                    "workflow.version",
                    workflow_version,
                )
                span.set_attribute(
                    "plan.step_count",
                    len(plan.steps),
                )

                with workflow_execution_duration_seconds.time():
                    with self.dataset_storage.open(
                        storage_key=dataset.storage_key
                    ) as source:
                        for chunk in self.streaming_reader.stream(
                            dataset.filename,
                            source,
                        ):
                            chunk_inputs = dict(inputs)
                            chunk_inputs["frame"] = chunk

                            trace_collector = ExecutionTraceCollector(
                                execution_id=execution_id
                            )

                            execute_plan = (
                                self.capability_execution.execute_plan
                            )
                            parameters = inspect.signature(
                                execute_plan
                            ).parameters

                            kwargs = {
                                "plan": plan,
                                "inputs": chunk_inputs,
                                "execution_id": execution_id,
                            }

                            if "trace_collector" in parameters:
                                kwargs["trace_collector"] = trace_collector

                            if "lineage_context" in parameters:
                                kwargs["lineage_context"] = lineage_context

                            result = execute_plan(**kwargs)

                            trace = getattr(
                                result,
                                "trace",
                                None,
                            ) or trace_collector.trace()

                            if (
                                self.trace_persistence is not None
                                and trace is not None
                            ):
                                self.trace_persistence.save(trace)

                            processed_chunks += 1

                            chunk_outputs = getattr(
                                result,
                                "outputs",
                                {},
                            ) or {}
                            chunk_row_count = chunk_outputs.get(
                                "processed_rows"
                            )

                            if isinstance(chunk_row_count, int):
                                processed_rows += chunk_row_count
                            else:
                                try:
                                    processed_rows += len(chunk)
                                except TypeError as exc:
                                    raise TypeError(
                                        "Streaming reader chunks must support len()"
                                    ) from exc

                    completed = runtime.complete(
                        outputs={
                            "processed_chunks": processed_chunks,
                            "processed_rows": processed_rows,
                        }
                    )

                    record_workflow_state_transition(
                        workflow_id=workflow_id,
                        execution_id=execution_id,
                        from_state="RUNNING",
                        to_state="COMPLETED",
                    )

                    workflow_executions_total.labels(
                        status="success"
                    ).inc()

                    if self.executions is not None:
                        self.executions.complete(
                            execution_id=execution_id,
                            outputs_json=json.dumps(
                                completed.outputs,
                                default=str,
                            ),
                        )

                    return completed

        except Exception as exc:
            workflow_executions_total.labels(
                status="error"
            ).inc()

            trace = getattr(
                exc,
                "execution_trace",
                None,
            )

            if (
                self.trace_persistence is not None
                and trace is not None
                and trace.records
            ):
                self.trace_persistence.save(trace)

            failed = runtime.fail(
                error=str(exc)
            )

            record_workflow_state_transition(
                workflow_id=workflow_id,
                execution_id=execution_id,
                from_state="RUNNING",
                to_state="FAILED",
            )

            if self.executions is not None:
                self.executions.fail(
                    execution_id=execution_id,
                    error=str(exc),
                )

            return failed

    def _execute_runtime(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        plan,
        inputs: dict[str, Any],
        dataset_id: str | None = None,
    ) -> WorkflowExecution:

        lineage_context = None

        if dataset_id is not None:
            lineage_context = {
                "dataset_id": dataset_id,
                "workflow_id": workflow_id,
                "workflow_version": workflow_version,
            }

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

            kwargs = {
                "plan": plan,
                "inputs": inputs,
                "execution_id": execution_id,
            }

            if "trace_collector" in parameters:
                kwargs["trace_collector"] = trace_collector

            if (
                lineage_context is not None
                and "lineage_context" in parameters
            ):
                kwargs["lineage_context"] = lineage_context

            with tracer(__name__).start_as_current_span(
                "workflow.execute"
            ) as span:
                span.set_attribute(
                    "execution.id",
                    execution_id,
                )
                span.set_attribute(
                    "workflow.id",
                    workflow_id,
                )
                span.set_attribute(
                    "workflow.version",
                    workflow_version,
                )
                span.set_attribute(
                    "plan.step_count",
                    len(plan.steps),
                )

                with workflow_execution_duration_seconds.time():
                    result = execute_plan(**kwargs)

            workflow_executions_total.labels(
                status="success"
            ).inc()

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
            workflow_executions_total.labels(
                status="error"
            ).inc()

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

            record_workflow_state_transition(
                workflow_id=workflow_id,
                execution_id=execution_id,
                from_state="RUNNING",
                to_state="FAILED",
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

        record_workflow_state_transition(
            workflow_id=workflow_id,
            execution_id=execution_id,
            from_state="RUNNING",
            to_state="COMPLETED",
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

    def recover(self, execution_id: str) -> None:
        """Fail a reclaimed delivery whose prior worker died while RUNNING.

        Redis pending-message recovery invokes this only after the delivery
        lease expired. Work is not replayed because capability side effects
        may not be idempotent.
        """
        failed = self._executions.fail_if_running(
            execution_id=execution_id,
            error=(
                "Worker delivery was reclaimed after its lease expired; "
                "execution was marked FAILED and was not retried"
            ),
        )
        if failed is not None:
            record_workflow_state_transition(
                workflow_id=failed.workflow_id,
                execution_id=execution_id,
                from_state="RUNNING",
                to_state="FAILED",
            )
