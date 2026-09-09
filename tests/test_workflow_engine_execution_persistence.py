from database.models import make_session_factory

from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)

from execution.workflow.engine import WorkflowEngine


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


class FakeCapabilityExecution:

    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
    ):

        class Result:
            outputs = {
                "result": "ok"
            }

        return Result()


def test_workflow_engine_persists_execution():

    sessions = make_session_factory(
        "sqlite://"
    )

    repo = WorkflowExecutionRepository(
        sessions
    )


    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        executions=repo,
        capability_execution=(
            FakeCapabilityExecution()
        ),
    )


    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv"
        },
    )


    assert runtime.outputs == {
        "result": "ok"
    }


    record = repo.get(
        "exec-1"
    )

    assert record is not None

    assert record.status == "COMPLETED"

    assert record.outputs_json == (
        '{"result": "ok"}'
    )
