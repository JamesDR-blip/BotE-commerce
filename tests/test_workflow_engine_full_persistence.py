from datetime import datetime, timezone
from database.models import make_session_factory

from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)

from services.workflow_engine import WorkflowEngine
from services.execution_trace_persistence import (
    ExecutionTracePersistence,
)


class FakeWorkflow:
    def get(self, workflow_id):
        return object()

    def get_active_version(self, workflow_id):
        return type(
            "Version",
            (),
            {
                "version": "1.0",
                "plan_json": {
                    "version": "1.0",
                    "steps": [],
                    "metadata": {},
                },
            },
        )()


class FakeCapabilityExecution:
    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
    ):
        record = type(
            "TraceRecord",
            (),
            {
                "capability_id": "data.validate",
                "capability_version": "1.0",
                "status": type(
                    "Status",
                    (),
                    {"value": "COMPLETED"},
                )(),
                "inputs": {
                    "file": "products.csv",
                },
                "outputs": {
                    "result": "ok",
                },
                "started_at": datetime.now(timezone.utc),
                "finished_at": datetime.now(timezone.utc),
                "error": None,
            },
        )()

        trace = type(
            "Trace",
            (),
            {
                "execution_id": execution_id,
                "records": (record,),
            },
        )()

        return type(
            "Result",
            (),
            {
                "outputs": {
                    "result": "ok",
                },
                "trace": trace,
            },
        )()


def test_workflow_engine_persists_execution_and_trace():
    sessions = make_session_factory("sqlite://")

    executions = WorkflowExecutionRepository(
        sessions
    )

    traces = CapabilityExecutionTraceRepository(
        sessions
    )

    trace_persistence = ExecutionTracePersistence(
        traces
    )

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        executions=executions,
        capability_execution=FakeCapabilityExecution(),
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv"
        },
    )

    assert runtime.success is True
    assert runtime.outputs == {
        "result": "ok"
    }

    execution = executions.get(
        "exec-1"
    )

    assert execution is not None
    assert execution.status == "COMPLETED"

    trace_records = traces.list_by_execution(
        "exec-1"
    )

    assert len(trace_records) == 1

    trace = trace_records[0]

    assert trace.execution_id == "exec-1"
    assert trace.capability_id == "data.validate"
    assert trace.capability_version == "1.0"
    assert trace.status == "COMPLETED"