from execution.workflow.engine import WorkflowEngine


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
                    "steps": [],
                    "version": "1.0",
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
        trace = type(
            "Trace",
            (),
            {
                "execution_id": execution_id,
                "records": (),
            },
        )()

        return type(
            "Result",
            (),
            {
                "outputs": {},
                "trace": trace,
            },
        )()


class FakeTracePersistence:
    def __init__(self):
        self.saved = []

    def save(self, trace):
        self.saved.append(trace)


def test_workflow_engine_persists_trace():
    trace_persistence = FakeTracePersistence()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=FakeCapabilityExecution(),
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv",
        },
    )

    assert runtime.success is True

    assert len(trace_persistence.saved) == 1

    saved_trace = trace_persistence.saved[0]

    assert saved_trace.execution_id == "exec-1"

def test_workflow_engine_persists_trace_exactly_once():
    trace_persistence = FakeTracePersistence()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=FakeCapabilityExecution(),
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv",
        },
    )

    assert runtime.success is True

    assert len(trace_persistence.saved) == 1

    saved_trace = trace_persistence.saved[0]

    assert saved_trace.execution_id == "exec-1"
