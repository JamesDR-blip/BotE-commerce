from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, DatasetRecord
from domain.changeset import (
    ChangeSet,
    ChangeSetItem,
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
    status: ChangeSetStatus = ChangeSetStatus.PREPARED,
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
    storage_key: str = "datasets/dataset-1/before.csv",
    content_hash: str = "b" * 64,
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


def test_changeset_repository_persists_changeset_and_items() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    changeset = make_changeset()
    items = [
        ChangeSetItem(
            id="item-1",
            changeset_id=changeset.id,
            entity="dataset_row",
            record_id="row-0",
            before_snapshot={"name": "Old"},
            after_snapshot={"name": "New"},
        )
    ]

    stored = repository.create(changeset, items)

    assert stored.id == "cs-1"
    assert stored.status is ChangeSetStatus.PREPARED
    assert stored.before_storage_key == (
        "datasets/dataset-1/before.csv"
    )

    loaded = repository.get("cs-1")

    assert loaded is not None
    assert loaded.id == "cs-1"
    assert loaded.status is ChangeSetStatus.PREPARED

    with sessions() as session:
        rows = session.query(
            __import__(
                "database.models",
                fromlist=["ChangeSetItemRecord"],
            ).ChangeSetItemRecord
        ).all()

        assert len(rows) == 1
        assert rows[0].record_id == "row-0"
        assert rows[0].before_snapshot == {"name": "Old"}
        assert rows[0].after_snapshot == {"name": "New"}


def test_changeset_repository_applies_prepared_changeset_atomically() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(),
        [],
    )

    with sessions() as session:
        with session.begin():
            applied = repository.apply_in_transaction(
                session,
                changeset_id="cs-1",
                expected_before_storage_key=(
                    "datasets/dataset-1/before.csv"
                ),
            )

        assert applied.status == ChangeSetStatus.APPLIED.value

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

    loaded = repository.get("cs-1")

    assert loaded is not None
    assert loaded.status is ChangeSetStatus.APPLIED
    assert loaded.applied_at is not None


def test_changeset_repository_rejects_apply_when_dataset_pointer_changed() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    create_dataset(
        sessions,
        storage_key="datasets/dataset-1/unexpected.csv",
        content_hash="x" * 64,
    )
    repository.create(
        make_changeset(),
        [],
    )

    with sessions() as session:
        with pytest.raises(ValueError, match="storage pointer changed"):
            with session.begin():
                repository.apply_in_transaction(
                    session,
                    changeset_id="cs-1",
                    expected_before_storage_key=(
                        "datasets/dataset-1/before.csv"
                    ),
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
            "datasets/dataset-1/unexpected.csv"
        )
        assert dataset.content_hash == "x" * 64


def test_changeset_repository_rolls_back_applied_changeset() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(),
        [],
    )

    with sessions() as session:
        with session.begin():
            repository.apply_in_transaction(
                session,
                changeset_id="cs-1",
                expected_before_storage_key=(
                    "datasets/dataset-1/before.csv"
                ),
            )

    with sessions() as session:
        with session.begin():
            rolled_back = repository.rollback_in_transaction(
                session,
                changeset_id="cs-1",
                expected_after_storage_key=(
                    "datasets/dataset-1/after.csv"
                ),
            )

        assert rolled_back.status == (
            ChangeSetStatus.ROLLED_BACK.value
        )

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

    loaded = repository.get("cs-1")

    assert loaded is not None
    assert loaded.status is ChangeSetStatus.ROLLED_BACK
    assert loaded.rolled_back_at is not None


def test_changeset_repository_transaction_rolls_back_dataset_and_changeset() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(),
        [],
    )

    with sessions() as session:
        with pytest.raises(RuntimeError, match="force rollback"):
            with session.begin():
                repository.apply_in_transaction(
                    session,
                    changeset_id="cs-1",
                    expected_before_storage_key=(
                        "datasets/dataset-1/before.csv"
                    ),
                )

                raise RuntimeError("force rollback")

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
            "datasets/dataset-1/before.csv"
        )
        assert dataset.content_hash == "b" * 64
