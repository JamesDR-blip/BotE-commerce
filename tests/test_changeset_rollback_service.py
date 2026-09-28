from datetime import datetime, timezone
from io import BytesIO

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.changesets.rollback_service import (
    ChangeSetRollbackService,
)
from database.models import (
    Base,
    ChangeSetRecord,
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
        before_content_hash="6ec3db418ab364e7ece99f3b79ccfa239edb33917eed2e46e1c56b97915fdc2c",
        after_storage_key="datasets/dataset-1/after.csv",
        after_content_hash="8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def create_dataset(
    sessions,
    *,
    dataset_id: str = "dataset-1",
    storage_key: str = "datasets/dataset-1/after.csv",
    content_hash: str = "8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad",
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


class FakeDatasetStorage:
    def __init__(self):
        self.contents = {
            "datasets/dataset-1/before.csv": b"before-artifact",
            "datasets/dataset-1/after.csv": b"after-artifact",
        }

    def open(self, *, storage_key: str):
        return BytesIO(self.contents[storage_key])


def create_service(sessions, *, with_audit=False, dataset_storage=None):
    repository = ChangeSetRepository(sessions)

    if dataset_storage is None:
        dataset_storage = FakeDatasetStorage()

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
            dataset_storage=dataset_storage,
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
        actor_id="user-1",
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
        assert dataset.content_hash == "6ec3db418ab364e7ece99f3b79ccfa239edb33917eed2e46e1c56b97915fdc2c"


def test_rollback_service_rejects_missing_changeset() -> None:
    sessions = create_session()
    service, _ = create_service(sessions)

    with pytest.raises(
        ValueError,
        match="ChangeSet not found",
    ):
        service.rollback(
            changeset_id="missing",
            actor_id="user-1",
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
        service.rollback(changeset_id="cs-1", actor_id="user-1")

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
        assert dataset.content_hash == "8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad"


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
        service.rollback(changeset_id="cs-1", actor_id="user-1")

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
        assert dataset.content_hash == "8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad"


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
        "before_content_hash": "6ec3db418ab364e7ece99f3b79ccfa239edb33917eed2e46e1c56b97915fdc2c",
        "after_storage_key": (
            "datasets/dataset-1/after.csv"
        ),
        "after_content_hash": "8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad",
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


def test_rollback_service_rejects_cross_owner_actor() -> None:
    sessions = create_session()
    service, repository = create_service(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(status=ChangeSetStatus.APPLIED),
        [],
    )

    with pytest.raises(PermissionError, match="not authorized"):
        service.rollback(
            changeset_id="cs-1",
            actor_id="owner-2",
        )










def test_rollback_service_rejects_tampered_after_artifact() -> None:
    sessions = create_session()
    storage = FakeDatasetStorage()
    service, repository = create_service(
        sessions,
        dataset_storage=storage,
    )

    create_dataset(sessions)
    repository.create(make_changeset(status=ChangeSetStatus.APPLIED), [])
    storage.contents["datasets/dataset-1/after.csv"] = b"tampered-after-artifact"

    with pytest.raises(ValueError, match="after artifact hash mismatch"):
        service.rollback(changeset_id="cs-1", actor_id="user-1")

    with sessions() as session:
        dataset = session.get(DatasetRecord, "dataset-1")
        changeset = session.get(ChangeSetRecord, "cs-1")
        assert dataset is not None
        assert changeset is not None
        assert dataset.storage_key == "datasets/dataset-1/after.csv"
        assert dataset.content_hash == "8f01b524dd9a2744f3525a91da871dad2412b0a58fd2aee88fae786f1af358ad"
        assert changeset.status == ChangeSetStatus.APPLIED
