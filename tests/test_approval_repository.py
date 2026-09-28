from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    ApprovalRecord,
    Base,
    ChangeSetRecord,
    DatasetRecord,
    ProjectRecord,
    UserRecord,
    WorkflowExecutionRecord,
    WorkflowRecord,
    WorkspaceRecord,
)
from domain.approval import ApprovalRequest
from infrastructure.persistence.approval_repository import ApprovalRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def create_parent_records(sessions) -> None:
    now = datetime.now(timezone.utc)

    with sessions() as session:
        session.add(
            UserRecord(
                id="user-1",
                email="test@example.com",
                display_name="Test User",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="test-workspace",
            )
        )
        session.add(
            ProjectRecord(
                id="project-1",
                workspace_id="workspace-1",
                name="test-project",
            )
        )
        session.add(
            DatasetRecord(
                id="dataset-1",
                project_id="project-1",
                name="catalog.csv",
                source_type="upload",
                status="READY",
                storage_key="datasets/dataset-1/before.csv",
                content_hash="b" * 64,
            )
        )
        session.add(
            WorkflowRecord(
                id="workflow-1",
                project_id="project-1",
                name="test-workflow",
            )
        )
        session.add(
            WorkflowExecutionRecord(
                id="execution-1",
                workflow_id="workflow-1",
                dataset_id="dataset-1",
                workflow_version="1.0",
                status="COMPLETED",
                inputs_json="{}",
                created_at=now,
            )
        )
        session.add(
            ChangeSetRecord(
                id="changeset-1",
                dataset_id="dataset-1",
                execution_id="execution-1",
                workflow_id="workflow-1",
                workflow_version="1.0",
                before_storage_key="datasets/dataset-1/before.csv",
                before_content_hash="b" * 64,
                after_storage_key="changesets/changeset-1/after.csv",
                after_content_hash="a" * 64,
                integrity_hash="3261b41ee867d64579fb2532da067e6d5f674a6be81bf72ee2c2ec8c4b3edaec",
                status="PREPARED",
                created_at=now,
            )
        )
        session.commit()


def test_approval_repository_persists_changeset_id() -> None:
    sessions = create_session()
    create_parent_records(sessions)

    repository = ApprovalRepository(sessions)

    request = ApprovalRequest(
        approval_id="approval-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        risk_score="HIGH",
        confidence_score=0.85,
        requested_by="requester",
        created_at=datetime.now(timezone.utc),
    )

    repository.create(
        request,
        token_hash="t" * 64,
    )

    with sessions() as session:
        record = session.get(ApprovalRecord, "approval-1")

        assert record is not None
        assert record.changeset_id == "changeset-1"
        assert record.execution_id == "execution-1"
def test_approval_repository_get_by_execution_id_returns_newest_first() -> None:
    sessions = create_session()
    create_parent_records(sessions)

    repository = ApprovalRepository(sessions)

    first = ApprovalRequest(
        approval_id="approval-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        risk_score="HIGH",
        confidence_score=0.80,
        requested_by="requester",
        created_at=datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc),
    )
    second = ApprovalRequest(
        approval_id="approval-2",
        execution_id="execution-1",
        changeset_id="changeset-1",
        risk_score="CRITICAL",
        confidence_score=0.70,
        requested_by="requester",
        created_at=datetime(2026, 9, 16, 11, 0, tzinfo=timezone.utc),
    )

    repository.create(first, token_hash="a" * 64)
    repository.create(second, token_hash="b" * 64)

    approvals = repository.get_by_execution_id("execution-1")

    assert [approval.approval_id for approval in approvals] == [
        "approval-2",
        "approval-1",
    ]


def test_approval_repository_get_by_execution_id_is_execution_scoped() -> None:
    sessions = create_session()
    create_parent_records(sessions)

    repository = ApprovalRepository(sessions)

    request = ApprovalRequest(
        approval_id="approval-1",
        execution_id="execution-1",
        changeset_id="changeset-1",
        risk_score="HIGH",
        confidence_score=0.85,
        requested_by="requester",
        created_at=datetime.now(timezone.utc),
    )

    repository.create(
        request,
        token_hash="t" * 64,
    )

    assert repository.get_by_execution_id("other-execution") == []
