from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.changesets.rollback_service import (
    ChangeSetRollbackService,
)
from database.models import Base, DatasetRecord
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


def create_service(sessions):
    repository = ChangeSetRepository(sessions)

    return (
        ChangeSetRollbackService(
            sessions=sessions,
            changesets=repository,
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
