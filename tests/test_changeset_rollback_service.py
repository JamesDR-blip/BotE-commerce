from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.changesets.rollback_service import (
    ChangeSetRollbackService,
)
from database.models import (
    Base,
    DatasetRecord,
    ProjectRecord,
    UserRecord,
    WorkspaceRecord,
)
from application.audit.audit_service import AuditService
from repositories.audit_events import AuditEventRepository
from domain.changeset import (
    ChangeSet,
    ChangeSetStatus,
)
from repositories.changesets import ChangeSetRepository


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def make_changeset(
    *,
    changeset_id: str = "cs-1",
    dataset_id: str = "dataset-1",
    status: ChangeSetStatus = ChangeSetStatus.APPLIED,
) -> ChangeSet:
    return ChangeSet(
        id=changeset_id,
        dataset_id=dataset_id,
        execution_id="execution-1",
        workflow_id="workflow-1",
        workflow_version="1.0",
        before_storage_key="datasets/dataset-1/before.csv",
        before_content_hash="b" * 64,
        after_storage_key="datasets/dataset-1/after.csv",
        after_content_hash="a" * 64,
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def create_dataset(
    sessions,
    *,
    dataset_id: str = "dataset-1",
    storage_key: str = "datasets/dataset-1/after.csv",
    content_hash: str = "a" * 64,
) -> None:
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
                id=dataset_id,
                project_id="project-1",
                name="catalog.csv",
                source_type="upload",
                status="READY",
                storage_key=storage_key,
                content_hash=content_hash,
            )
        )
        session.commit()


def create_service(sessions, *, with_audit=False):
    repository = ChangeSetRepository(sessions)

    audit_service = None

    if with_audit:
        audit_service = AuditService(
            sessions=sessions,
            repository=AuditEventRepository(sessions),
        )

    return (
        ChangeSetRollbackService(
            sessions=sessions,
            changesets=repository,
            audit_service=audit_service,
        ),
        repository,
    )


def test_rollback_service_rolls_back_applied_changeset() -> None:
    sessions = create_session()
    service, repository = create_service(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(
            status=ChangeSetStatus.APPLIED,
        ),
        [],
    )

    rolled_back = service.rollback(
        changeset_id="cs-1",
    )

    assert rolled_back.id == "cs-1"
    assert rolled_back.status is ChangeSetStatus.ROLLED_BACK
    assert rolled_back.rolled_back_at is not None

    with sessions() as session:
        dataset = session.get(
            DatasetRecord,
            "dataset-1",
        )

        assert dataset is not None
        assert dataset.storage_key == (
            "datasets/dataset-1/before.csv"
        )
        assert dataset.content_hash == "b" * 64


def test_rollback_service_rejects_missing_changeset() -> None:
    sessions = create_session()
    service, _ = create_service(sessions)

    with pytest.raises(
        ValueError,
        match="ChangeSet not found",
    ):
        service.rollback(
            changeset_id="missing",
        )


def test_rollback_service_rejects_non_applied_changeset() -> None:
    sessions = create_session()
    service, repository = create_service(sessions)

    create_dataset(sessions)

    repository.create(
        make_changeset(
            status=ChangeSetStatus.PREPARED,
        ),
        [],
    )

    with pytest.raises(
        ValueError,
        match="Only APPLIED ChangeSets can be rolled back",
    ):
        service.rollback(
            changeset_id="cs-1",
        )

    loaded = repository.get("cs-1")

    assert loaded is not None
    assert loaded.status is ChangeSetStatus.PREPARED

    with sessions() as session:
        dataset = session.get(
            DatasetRecord,
            "dataset-1",
        )

        assert dataset is not None
        assert dataset.storage_key == (
            "datasets/dataset-1/after.csv"
        )
        assert dataset.content_hash == "a" * 64


def test_rollback_transaction_rolls_back_dataset_and_changeset(
    monkeypatch,
) -> None:
    sessions = create_session()
    service, repository = create_service(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(
            status=ChangeSetStatus.APPLIED,
        ),
        [],
    )

    original_rollback = repository.rollback_in_transaction

    def failing_rollback(*args, **kwargs):
        record = original_rollback(*args, **kwargs)
        raise RuntimeError("force rollback")

    monkeypatch.setattr(
        repository,
        "rollback_in_transaction",
        failing_rollback,
    )

    with pytest.raises(
        RuntimeError,
        match="force rollback",
    ):
        service.rollback(
            changeset_id="cs-1",
        )

    loaded = repository.get("cs-1")

    assert loaded is not None
    assert loaded.status is ChangeSetStatus.APPLIED
    assert loaded.rolled_back_at is None

    with sessions() as session:
        dataset = session.get(
            DatasetRecord,
            "dataset-1",
        )

        assert dataset is not None
        assert dataset.storage_key == (
            "datasets/dataset-1/after.csv"
        )
        assert dataset.content_hash == "a" * 64


def test_rollback_service_records_audit_event_with_actor_and_metadata() -> None:
    sessions = create_session()
    service, repository = create_service(
        sessions,
        with_audit=True,
    )

    create_dataset(sessions)
    repository.create(
        make_changeset(
            status=ChangeSetStatus.APPLIED,
        ),
        [],
    )

    rolled_back = service.rollback(
        changeset_id="cs-1",
        actor_id="user-1",
    )

    assert rolled_back.status is ChangeSetStatus.ROLLED_BACK

    audit_repository = AuditEventRepository(sessions)

    with sessions() as session:
        events = audit_repository.list_for_owner(
            owner_id="user-1",
        )

    assert len(events) == 1

    event = events[0]

    assert event.workspace_id == "workspace-1"
    assert event.actor_id == "user-1"
    assert event.action == "CHANGESET_ROLLED_BACK"
    assert event.resource_type == "changeset"
    assert event.resource_id == "cs-1"
    assert event.execution_id == "execution-1"
    assert event.changeset_id == "cs-1"
    assert event.metadata == {
        "dataset_id": "dataset-1",
        "status": "ROLLED_BACK",
        "before_storage_key": (
            "datasets/dataset-1/before.csv"
        ),
        "before_content_hash": "b" * 64,
        "after_storage_key": (
            "datasets/dataset-1/after.csv"
        ),
        "after_content_hash": "a" * 64,
    }
    assert event.previous_hash is None
    assert len(event.event_hash) == 64


def test_rollback_service_does_not_persist_audit_on_transaction_failure(
    monkeypatch,
) -> None:
    sessions = create_session()
    service, repository = create_service(
        sessions,
        with_audit=True,
    )

    create_dataset(sessions)
    repository.create(
        make_changeset(
            status=ChangeSetStatus.APPLIED,
        ),
        [],
    )

    original_rollback = repository.rollback_in_transaction

    def failing_rollback(*args, **kwargs):
        record = original_rollback(*args, **kwargs)
        raise RuntimeError("force rollback")

    monkeypatch.setattr(
        repository,
        "rollback_in_transaction",
        failing_rollback,
    )

    with pytest.raises(
        RuntimeError,
        match="force rollback",
    ):
        service.rollback(
            changeset_id="cs-1",
            actor_id="user-1",
        )

    audit_repository = AuditEventRepository(sessions)

    with sessions() as session:
        events = audit_repository.list_for_owner(
            owner_id="user-1",
        )

    assert events == []
