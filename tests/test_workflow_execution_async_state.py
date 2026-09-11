import pytest

from database.models import make_session_factory
from domain.workflow_execution_status import (
    WorkflowExecutionStatus,
)
from repositories.workflow_executions import (
    WorkflowExecutionRepository,
)


def test_workflow_execution_status_includes_queued():
    assert WorkflowExecutionStatus.QUEUED.value == "QUEUED"


def test_queued_execution_can_be_atomically_claimed():
    sessions = make_session_factory("sqlite://")
    repo = WorkflowExecutionRepository(sessions)

    repo.create(
        execution_id="exec-queued",
        workflow_id="wf-1",
        workflow_version="1.0",
        status="QUEUED",
        inputs_json="{}",
    )

    claimed = repo.claim_running("exec-queued")

    assert claimed is not None
    assert claimed.status == "RUNNING"
    assert claimed.started_at is not None

    stored = repo.get("exec-queued")

    assert stored is not None
    assert stored.status == "RUNNING"


def test_queued_execution_can_only_be_claimed_once():
    sessions = make_session_factory("sqlite://")
    repo = WorkflowExecutionRepository(sessions)

    repo.create(
        execution_id="exec-queued",
        workflow_id="wf-1",
        workflow_version="1.0",
        status="QUEUED",
        inputs_json="{}",
    )

    first_claim = repo.claim_running("exec-queued")
    second_claim = repo.claim_running("exec-queued")

    assert first_claim is not None
    assert first_claim.status == "RUNNING"
    assert second_claim is None


def test_non_queued_execution_cannot_be_claimed():
    sessions = make_session_factory("sqlite://")
    repo = WorkflowExecutionRepository(sessions)

    repo.create(
        execution_id="exec-created",
        workflow_id="wf-1",
        workflow_version="1.0",
        status="CREATED",
        inputs_json="{}",
    )

    claimed = repo.claim_running("exec-created")

    assert claimed is None

    stored = repo.get("exec-created")

    assert stored is not None
    assert stored.status == "CREATED"


def test_terminal_execution_cannot_be_claimed():
    sessions = make_session_factory("sqlite://")
    repo = WorkflowExecutionRepository(sessions)

    repo.create(
        execution_id="exec-completed",
        workflow_id="wf-1",
        workflow_version="1.0",
        status="COMPLETED",
        inputs_json="{}",
    )

    claimed = repo.claim_running("exec-completed")

    assert claimed is None

    with pytest.raises(ValueError):
        repo.complete(
            execution_id="exec-completed",
            outputs_json="{}",
        )
