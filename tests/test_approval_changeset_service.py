from datetime import datetime, timezone
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.approval.approval_changeset_service import (
    ApprovalChangeSetService,
)
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
from infrastructure.persistence.approval_repository import ApprovalRepository
from repositories.changesets import ChangeSetRepository
from repositories.audit_events import AuditEventRepository
from application.audit.audit_service import AuditService
from repositories.workflow_executions import WorkflowExecutionRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def create_parent_records(
    sessions,
    *,
    execution_status="PENDING_APPROVAL",
    dataset_storage_key="datasets/dataset-1/before.csv",
):
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
                storage_key=dataset_storage_key,
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
                status=execution_status,
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
        session.add(
            ApprovalRecord(
                approval_id="approval-1",
                execution_id="execution-1",
                changeset_id="changeset-1",
                risk_score="HIGH",
                confidence_score=0.85,
                requested_by="requester",
                created_at=now,
                decision=None,
                token_hash="t" * 64,
            )
        )
        session.commit()


def test_approval_changeset_service_commits_atomically():
    sessions = create_session()
    create_parent_records(sessions)

    approvals = ApprovalRepository(sessions)
    changesets = ChangeSetRepository(sessions)
    workflow_executions = WorkflowExecutionRepository(sessions)

    audit_repository = AuditEventRepository(sessions)
    audit_service = AuditService(
        sessions=sessions,
        repository=audit_repository,
    )

    service = ApprovalChangeSetService(
        sessions=sessions,
        approvals=approvals,
        changesets=changesets,
        workflow_executions=workflow_executions,
        audit_service=audit_service,
    )

    service.apply(
        approval_id="approval-1",
        actor_id="user-1",
    )

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        changeset = session.get(ChangeSetRecord, "changeset-1")
        approval = session.get(ApprovalRecord, "approval-1")
        execution = session.get(
            WorkflowExecutionRecord,
            "execution-1",
        )

        assert dataset is not None
        assert changeset is not None
        assert approval is not None
        assert execution is not None

        assert dataset.storage_key == (
            "changesets/changeset-1/after.csv"
        )
        assert dataset.content_hash == "a" * 64

        assert changeset.status == "APPLIED"
        assert changeset.applied_at is not None

        assert approval.decision == "APPROVED"

        assert execution.status == "COMPLETED"
        assert execution.outputs_json is not None

        outputs = json.loads(execution.outputs_json)
        assert outputs == {
            "changeset_id": "changeset-1",
            "status": "APPLIED",
        }

        audit_events = audit_repository.list_for_owner(
            owner_id="user-1",
        )

        assert len(audit_events) == 1

        event = audit_events[0]

        assert event.workspace_id == "workspace-1"
        assert event.actor_id == "user-1"
        assert event.action == "APPROVAL_APPLIED"
        assert event.resource_type == "changeset"
        assert event.resource_id == "changeset-1"
        assert event.execution_id == "execution-1"
        assert event.changeset_id == "changeset-1"
        assert event.metadata == {
            "approval_id": "approval-1",
            "dataset_id": "dataset-1",
            "status": "APPLIED",
            "before_storage_key": (
                "datasets/dataset-1/before.csv"
            ),
            "before_content_hash": "b" * 64,
            "after_storage_key": (
                "changesets/changeset-1/after.csv"
            ),
            "after_content_hash": "a" * 64,
        }
        assert event.previous_hash is None
        assert len(event.event_hash) == 64


class FailingWorkflowExecutionRepository:
    def get_in_transaction(
        self,
        session,
        execution_id,
    ):
        return session.get(
            WorkflowExecutionRecord,
            execution_id,
        )

    def complete_after_approval_in_transaction(
        self,
        session,
        *,
        execution_id,
        outputs_json,
    ):
        raise RuntimeError("forced completion failure")


def test_approval_changeset_service_rolls_back_all_mutations_on_failure():
    sessions = create_session()
    create_parent_records(sessions)

    approvals = ApprovalRepository(sessions)
    changesets = ChangeSetRepository(sessions)

    audit_repository = AuditEventRepository(sessions)
    audit_service = AuditService(
        sessions=sessions,
        repository=audit_repository,
    )

    service = ApprovalChangeSetService(
        sessions=sessions,
        approvals=approvals,
        changesets=changesets,
        workflow_executions=FailingWorkflowExecutionRepository(),
        audit_service=audit_service,
    )

    with pytest.raises(
        RuntimeError,
        match="forced completion failure",
    ):
        service.apply(approval_id="approval-1")

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        changeset = session.get(ChangeSetRecord, "changeset-1")
        approval = session.get(ApprovalRecord, "approval-1")
        execution = session.get(
            WorkflowExecutionRecord,
            "execution-1",
        )

        assert dataset is not None
        assert changeset is not None
        assert approval is not None
        assert execution is not None

        assert dataset.storage_key == (
            "datasets/dataset-1/before.csv"
        )
        assert dataset.content_hash == "b" * 64

        assert changeset.status == "PREPARED"
        assert changeset.applied_at is None

        assert approval.decision is None

        assert execution.status == "PENDING_APPROVAL"
        assert execution.outputs_json is None

        audit_events = audit_repository.list_for_owner(
            owner_id="user-1",
        )

        assert audit_events == []


def test_approval_changeset_service_rejects_stale_dataset_pointer():
    sessions = create_session()
    create_parent_records(
        sessions,
        dataset_storage_key="datasets/dataset-1/unexpected.csv",
    )

    approvals = ApprovalRepository(sessions)
    changesets = ChangeSetRepository(sessions)
    workflow_executions = WorkflowExecutionRepository(sessions)

    service = ApprovalChangeSetService(
        sessions=sessions,
        approvals=approvals,
        changesets=changesets,
        workflow_executions=workflow_executions,
    )

    with pytest.raises(
        ValueError,
        match="Dataset storage pointer changed before ChangeSet could be applied",
    ):
        service.apply(approval_id="approval-1")

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        changeset = session.get(ChangeSetRecord, "changeset-1")
        approval = session.get(ApprovalRecord, "approval-1")
        execution = session.get(
            WorkflowExecutionRecord,
            "execution-1",
        )

        assert dataset is not None
        assert changeset is not None
        assert approval is not None
        assert execution is not None

        assert dataset.storage_key == (
            "datasets/dataset-1/unexpected.csv"
        )
        assert changeset.status == "PREPARED"
        assert approval.decision is None
        assert execution.status == "PENDING_APPROVAL"


def _assert_approval_changeset_integrity_rejected(
    sessions,
    *,
    dataset_id=None,
    workflow_id=None,
    workflow_version=None,
    expected_message,
):
    approvals = ApprovalRepository(sessions)
    changesets = ChangeSetRepository(sessions)
    workflow_executions = WorkflowExecutionRepository(sessions)

    with sessions() as session:
        execution = session.get(
            WorkflowExecutionRecord,
            "execution-1",
        )
        assert execution is not None

        if dataset_id is not None:
            execution.dataset_id = dataset_id
        if workflow_id is not None:
            execution.workflow_id = workflow_id
        if workflow_version is not None:
            execution.workflow_version = workflow_version

        session.commit()

    service = ApprovalChangeSetService(
        sessions=sessions,
        approvals=approvals,
        changesets=changesets,
        workflow_executions=workflow_executions,
    )

    with pytest.raises(ValueError, match=expected_message):
        service.apply(approval_id="approval-1")

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        changeset = session.get(ChangeSetRecord, "changeset-1")
        approval = session.get(ApprovalRecord, "approval-1")
        execution = session.get(
            WorkflowExecutionRecord,
            "execution-1",
        )

        assert dataset is not None
        assert changeset is not None
        assert approval is not None
        assert execution is not None

        assert dataset.storage_key == (
            "datasets/dataset-1/before.csv"
        )
        assert dataset.content_hash == "b" * 64
        assert changeset.status == "PREPARED"
        assert changeset.applied_at is None
        assert approval.decision is None
        assert execution.status == "PENDING_APPROVAL"


def test_approval_changeset_service_rejects_dataset_mismatch():
    sessions = create_session()
    create_parent_records(sessions)

    _assert_approval_changeset_integrity_rejected(
        sessions,
        dataset_id="dataset-other",
        expected_message=(
            "Workflow execution and ChangeSet dataset IDs do not match"
        ),
    )


def test_approval_changeset_service_rejects_workflow_mismatch():
    sessions = create_session()
    create_parent_records(sessions)

    _assert_approval_changeset_integrity_rejected(
        sessions,
        workflow_id="workflow-other",
        expected_message=(
            "Workflow execution and ChangeSet workflow IDs do not match"
        ),
    )


def test_approval_changeset_service_rejects_workflow_version_mismatch():
    sessions = create_session()
    create_parent_records(sessions)

    _assert_approval_changeset_integrity_rejected(
        sessions,
        workflow_version="2.0",
        expected_message=(
            "Workflow execution and ChangeSet workflow versions do not match"
        ),
    )
