from database.models import make_session_factory

from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)

from execution.workflow.engine import WorkflowEngine
from infrastructure.persistence.execution_trace import (
    ExecutionTracePersistence,
)



class FakeWorkflow:
    def get(self, workflow_id):
        return object()

    def get_active_version(self, workflow_id):
        class Version:
            version = "1.0"
            plan_json = """
            {
                "version": "1.0",
                "steps": [],
                "metadata": {}
            }
            """

        return Version()


class FailingCapabilityExecution:

    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
        trace_collector=None,
    ):
        if trace_collector is not None:
            index = trace_collector.start(
                "data.clean",
                "1.0",
                inputs={
                    "file": "products.csv",
                },
            )

            trace_collector.complete(
                index,
                {
                    "cleaned": True,
                },
            )

            index = trace_collector.start(
                "data.validate",
                "1.0",
                inputs={
                    "cleaned": True,
                },
            )

            trace_collector.fail(
                index,
                RuntimeError(
                    "Capability execution failed"
                ),
            )

        raise RuntimeError(
            "Capability execution failed"
        )


def test_workflow_engine_persists_failure():
    sessions = make_session_factory("sqlite://")

    executions = WorkflowExecutionRepository(
        sessions
    )

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        executions=executions,
        capability_execution=FailingCapabilityExecution(),
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-failed",
        inputs={
            "file": "products.csv"
        },
    )

    assert runtime.success is False

    assert runtime.status.value == "FAILED"

    assert runtime.error == (
        "Capability execution failed"
    )

    execution = executions.get(
        "exec-failed"
    )

    assert execution is not None

    assert execution.status == "FAILED"

    assert execution.error == (
        "Capability execution failed"
    )

    assert execution.workflow_version == "1.0"

    assert execution.started_at is not None

    assert execution.finished_at is not None

    assert execution.finished_at >= (
        execution.started_at
    )

def test_workflow_engine_persists_partial_trace_on_failure():

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
        capability_execution=FailingCapabilityExecution(),
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-partial-failure",
        inputs={
            "file": "products.csv"
        },
    )

    assert runtime.success is False

    assert runtime.status.value == "FAILED"

    assert runtime.error == (
        "Capability execution failed"
    )

    records = traces.list_by_execution(
        "exec-partial-failure"
    )

    assert len(records) == 2

    assert records[0].capability_id == "data.clean"
    assert records[0].status == "COMPLETED"

    assert records[1].capability_id == "data.validate"
    assert records[1].status == "FAILED"
    assert records[1].error == (
        "Capability execution failed"
    )
