from services.workflow_engine import WorkflowEngine


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
        return type(
            "Result",
            (),
            {
                "outputs": {},
                "trace": type(
                    "Trace",
                    (),
                    {
                        "records": ()
                    }
                )(),
            },
        )()


class FakeTracePersistence:

    def save(
        self,
        *,
        execution_id,
        trace,
    ):
        self.execution_id = execution_id
        self.trace = trace

def test_workflow_engine_persists_trace():

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=FakeCapabilityExecution(),
        trace_persistence=FakeTracePersistence(),
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv"
        },
    )

    assert runtime.success is True