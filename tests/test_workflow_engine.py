import json

from domain.plans import ExecutionPlan

from services.workflow_engine import WorkflowEngine


class FakeWorkflow:

    def get(self, workflow_id):
        return object()


    def get_active_version(
        self,
        workflow_id,
    ):

        class Version:
            version = "1.0"

            plan_json = json.dumps(
                {
                    "version": "1.0",
                    "steps": [],
                    "metadata": {},
                }
            )

        return Version()



def test_workflow_engine_loads_plan():

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=None,
    )


    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv"
        },
    )


    assert runtime.workflow_id == "wf-1"

    assert runtime.workflow_version == "1.0"

    assert isinstance(
        runtime.plan,
        ExecutionPlan,
    )

    assert runtime.plan.steps == ()