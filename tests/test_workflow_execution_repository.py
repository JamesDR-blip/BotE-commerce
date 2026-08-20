from database.models import make_session_factory
from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)


def test_create_and_get_workflow_execution():

    sessions = make_session_factory(
        "sqlite://"
    )

    repo = WorkflowExecutionRepository(
        sessions
    )

    item = repo.create(
        execution_id="exec-1",
        workflow_id="wf-1",
        workflow_version="1.0",
        status="RUNNING",
        inputs={
            "file": "products.csv"
        },
    )

    assert item.id == "exec-1"
    assert item.status == "RUNNING"


    loaded = repo.get(
        "exec-1"
    )

    assert loaded is not None
    assert loaded.workflow_id == "wf-1"


def test_workflow_execution_repository_lifecycle():

    sessions = make_session_factory(
        "sqlite://"
    )

    repo = WorkflowExecutionRepository(
        sessions
    )

    item = repo.create(
        execution_id="exec-1",
        workflow_id="wf-1",
        workflow_version="1.0",
        inputs_json="{}",
    )

    assert item.status == "CREATED"


    running = repo.mark_running(
        "exec-1"
    )

    assert running.status == "RUNNING"


    completed = repo.complete(
        execution_id="exec-1",
        outputs_json="{}",
    )

    assert completed.status == "COMPLETED"


    loaded = repo.get(
        "exec-1"
    )

    assert loaded is not None
    assert loaded.outputs_json == "{}"