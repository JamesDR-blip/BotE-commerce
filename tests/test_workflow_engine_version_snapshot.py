from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from repositories.workflows import WorkflowRepository
from repositories.workflow_executions import WorkflowExecutionRepository
from services.workflow_engine import WorkflowEngine


class FakeCapabilityExecution:
    def __init__(self):
        self.plans = {}

    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
    ):
        self.plans[execution_id] = plan

        return type(
            "Result",
            (),
            {
                "outputs": {},
                "trace": type(
                    "Trace",
                    (),
                    {
                        "execution_id": execution_id,
                        "records": (),
                    },
                )(),
            },
        )()


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def test_execution_keeps_workflow_version_snapshot():
    sessions = create_session()

    workflows = WorkflowRepository(sessions)
    executions = WorkflowExecutionRepository(sessions)

    workflows.create(
        workflow_id="wf-1",
        project_id="project-1",
        name="Validation",
        version="1.0",
        plan_json='''{
            "version": "1.0",
            "steps": [
                {
                    "capability_id": "data.clean",
                    "capability_version": "1.0",
                    "parameters": {},
                    "input_mapping": {}
                }
            ],
            "metadata": {}
        }''',
    )

    capability_execution = FakeCapabilityExecution()

    engine = WorkflowEngine(
        workflows=workflows,
        executions=executions,
        capability_execution=capability_execution,
    )

    first = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={"file": "v1.csv"},
    )

    assert first.success is True

    stored_first = executions.get("exec-1")

    assert stored_first is not None
    assert stored_first.workflow_version == "1.0"

    workflows.create_version(
        workflow_id="wf-1",
        version="2.0",
        plan_json='''{
            "version": "2.0",
            "steps": [
                {
                    "capability_id": "data.normalize",
                    "capability_version": "1.0",
                    "parameters": {},
                    "input_mapping": {}
                }
            ],
            "metadata": {}
        }''',
    )

    workflows.activate_version(
        "wf-1",
        "2.0",
    )

    second = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-2",
        inputs={"file": "v2.csv"},
    )

    assert second.success is True

    stored_first = executions.get("exec-1")
    stored_second = executions.get("exec-2")

    assert stored_first is not None
    assert stored_second is not None

    assert stored_first.workflow_version == "1.0"
    assert stored_second.workflow_version == "2.0"

    first_plan = capability_execution.plans["exec-1"]
    second_plan = capability_execution.plans["exec-2"]

    assert first_plan.version == "1.0"
    assert first_plan.steps[0].capability_id == "data.clean"

    assert second_plan.version == "2.0"
    assert second_plan.steps[0].capability_id == "data.normalize"