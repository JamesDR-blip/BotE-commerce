import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def create_execution(repo, execution_id="exec-1"):
    return repo.create(
        execution_id=execution_id,
        workflow_id="wf-1",
        workflow_version="1.0",
        inputs_json="{}",
    )


def test_execution_starts_created():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    record = create_execution(repo)

    assert record.status == "CREATED"


def test_execution_can_move_from_created_to_running():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    create_execution(repo)

    record = repo.mark_running("exec-1")

    assert record.status == "RUNNING"
    assert record.started_at is not None


def test_execution_can_complete_from_running():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    create_execution(repo)
    repo.mark_running("exec-1")

    record = repo.complete(
        execution_id="exec-1",
        outputs_json="{}",
    )

    assert record.status == "COMPLETED"
    assert record.outputs_json == "{}"
    assert record.finished_at is not None


def test_execution_can_fail_from_running():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    create_execution(repo)
    repo.mark_running("exec-1")

    record = repo.fail(
        execution_id="exec-1",
        error="boom",
    )

    assert record.status == "FAILED"
    assert record.error == "boom"
    assert record.finished_at is not None


def test_completed_execution_is_terminal():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    create_execution(repo)
    repo.mark_running("exec-1")
    repo.complete(
        execution_id="exec-1",
        outputs_json="{}",
    )

    with pytest.raises(ValueError):
        repo.mark_running("exec-1")


def test_failed_execution_is_terminal():
    sessions = create_session()
    repo = WorkflowExecutionRepository(sessions)

    create_execution(repo)
    repo.mark_running("exec-1")
    repo.fail(
        execution_id="exec-1",
        error="boom",
    )

    with pytest.raises(ValueError):
        repo.complete(
            execution_id="exec-1",
            outputs_json="{}",
        )