from dataclasses import replace
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    Base,
    ChangeSetRecord,
    DatasetRecord,
    ProjectRecord,
    WorkspaceRecord,
)
from domain.changeset import (
    ChangeSet,
    ChangeSetItem,
    ChangeSetStatus,
    compute_changeset_integrity_hash,
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


def create_owner_path(
    sessions,
    *,
    workspace_id: str,
    owner_id: str,
    project_id: str,
    dataset_id: str,
) -> None:
    with sessions() as session:
        session.add_all(
            [
                WorkspaceRecord(
                    id=workspace_id,
                    owner_id=owner_id,
                    name=f"Workspace {workspace_id}",
                ),
                ProjectRecord(
                    id=project_id,
                    workspace_id=workspace_id,
                    name=f"Project {project_id}",
                ),
                DatasetRecord(
                    id=dataset_id,
                    project_id=project_id,
                    name=f"Dataset {dataset_id}",
                    source_type="upload",
                    status="READY",
                ),
            ]
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
    assert stored.before_storage_key == ("datasets/dataset-1/before.csv")

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


def test_changeset_repository_persists_integrity_hash() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    changeset = make_changeset()
    stored = repository.create(changeset, [])

    expected = compute_changeset_integrity_hash(changeset)

    assert stored.integrity_hash == expected

    with sessions() as session:
        record = session.get(ChangeSetRecord, "cs-1")
        assert record is not None
        assert record.integrity_hash == expected


def test_changeset_repository_detects_tampered_record_on_read() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    repository.create(make_changeset(), [])

    with sessions() as session:
        record = session.get(ChangeSetRecord, "cs-1")
        assert record is not None
        record.after_storage_key = "datasets/dataset-1/tampered.csv"
        session.commit()

    with pytest.raises(ValueError, match="integrity hash mismatch"):
        repository.get("cs-1")


def test_changeset_repository_detects_tampered_item_on_read() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)
    changeset = make_changeset()
    repository.create(
        changeset,
        [
            ChangeSetItem(
                id="item-1",
                changeset_id=changeset.id,
                entity="dataset_row",
                record_id="row-0",
                before_snapshot={"name": "Old"},
                after_snapshot={"name": "New"},
            )
        ],
    )

    with sessions() as session:
        record = session.get(ChangeSetRecord, "cs-1")
        assert record is not None
        record.items[0].after_snapshot = {"name": "Tampered"}
        session.commit()

    with pytest.raises(ValueError, match="integrity hash mismatch"):
        repository.get("cs-1")


def test_changeset_repository_rejects_mismatched_supplied_integrity_hash() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    changeset = make_changeset()
    changeset = replace(changeset, integrity_hash="0" * 64)

    with pytest.raises(ValueError, match="integrity hash mismatch"):
        repository.create(changeset, [])


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
                expected_before_storage_key=("datasets/dataset-1/before.csv"),
            )

        assert applied.status == ChangeSetStatus.APPLIED.value

    with sessions() as session:
        dataset = session.get(
            DatasetRecord,
            "dataset-1",
        )

        assert dataset is not None
        assert dataset.storage_key == ("datasets/dataset-1/after.csv")
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

    with (
        sessions() as session,
        pytest.raises(ValueError, match="storage pointer changed"),
        session.begin(),
    ):
        repository.apply_in_transaction(
            session,
            changeset_id="cs-1",
            expected_before_storage_key=("datasets/dataset-1/before.csv"),
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
        assert dataset.storage_key == ("datasets/dataset-1/unexpected.csv")
        assert dataset.content_hash == "x" * 64


def test_changeset_repository_rolls_back_applied_changeset() -> None:
    sessions = create_session()
    repository = ChangeSetRepository(sessions)

    create_dataset(sessions)
    repository.create(
        make_changeset(),
        [],
    )

    with sessions() as session, session.begin():
        repository.apply_in_transaction(
            session,
            changeset_id="cs-1",
            expected_before_storage_key=("datasets/dataset-1/before.csv"),
        )

    with sessions() as session:
        with session.begin():
            rolled_back = repository.rollback_in_transaction(
                session,
                changeset_id="cs-1",
                expected_after_storage_key=("datasets/dataset-1/after.csv"),
            )

        assert rolled_back.status == (ChangeSetStatus.ROLLED_BACK.value)

    with sessions() as session:
        dataset = session.get(
            DatasetRecord,
            "dataset-1",
        )

        assert dataset is not None
        assert dataset.storage_key == ("datasets/dataset-1/before.csv")
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

    with (
        sessions() as session,
        pytest.raises(RuntimeError, match="force rollback"),
        session.begin(),
    ):
        repository.apply_in_transaction(
            session,
            changeset_id="cs-1",
            expected_before_storage_key=("datasets/dataset-1/before.csv"),
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
        assert dataset.storage_key == ("datasets/dataset-1/before.csv")
        assert dataset.content_hash == "b" * 64


def test_changeset_repository_lists_only_owner_changesets_in_descending_order():
    sessions = create_session()
    repository = ChangeSetRepository(sessions)
    create_owner_path(
        sessions,
        workspace_id="ws-1",
        owner_id="owner-1",
        project_id="project-1",
        dataset_id="dataset-1",
    )
    create_owner_path(
        sessions,
        workspace_id="ws-2",
        owner_id="owner-2",
        project_id="project-2",
        dataset_id="dataset-2",
    )

    older = replace(
        make_changeset(changeset_id="cs-old"),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    newer = replace(
        make_changeset(changeset_id="cs-new"),
        created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    other_owner = make_changeset(
        changeset_id="cs-other",
        dataset_id="dataset-2",
    )
    repository.create(older, [])
    repository.create(newer, [])
    repository.create(other_owner, [])

    assert [
        changeset.id
        for changeset in repository.list_for_owner(owner_id="owner-1")
    ] == ["cs-new", "cs-old"]
    assert [
        changeset.id
        for changeset in repository.list_for_owner(owner_id="owner-2")
    ] == ["cs-other"]
    assert repository.list_for_owner(owner_id="owner-without-changesets") == []


def test_changeset_repository_get_for_owner_hides_foreign_and_missing_changesets():
    sessions = create_session()
    repository = ChangeSetRepository(sessions)
    create_owner_path(
        sessions,
        workspace_id="ws-1",
        owner_id="owner-1",
        project_id="project-1",
        dataset_id="dataset-1",
    )
    repository.create(make_changeset(), [])

    assert repository.get_for_owner(
        changeset_id="cs-1",
        owner_id="owner-1",
    ) is not None
    assert repository.get_for_owner(
        changeset_id="cs-1",
        owner_id="owner-2",
    ) is None
    assert repository.get_for_owner(
        changeset_id="missing",
        owner_id="owner-1",
    ) is None


def test_changeset_repository_lists_owner_items_in_record_id_order():
    sessions = create_session()
    repository = ChangeSetRepository(sessions)
    create_owner_path(
        sessions,
        workspace_id="ws-1",
        owner_id="owner-1",
        project_id="project-1",
        dataset_id="dataset-1",
    )
    items = [
        ChangeSetItem(
            id="item-b",
            changeset_id="cs-1",
            entity="dataset_row",
            record_id="b",
            before_snapshot={},
            after_snapshot={},
        ),
        ChangeSetItem(
            id="item-a",
            changeset_id="cs-1",
            entity="dataset_row",
            record_id="a",
            before_snapshot={},
            after_snapshot={},
        ),
    ]
    repository.create(make_changeset(), items)
    repository.create(make_changeset(changeset_id="cs-empty"), [])

    found_items = repository.list_items_for_owner(
        changeset_id="cs-1",
        owner_id="owner-1",
    )

    assert found_items is not None
    assert [item.record_id for item in found_items] == ["a", "b"]
    assert repository.list_items_for_owner(
        changeset_id="cs-1",
        owner_id="owner-2",
    ) is None
    assert repository.list_items_for_owner(
        changeset_id="missing",
        owner_id="owner-1",
    ) is None
    assert repository.list_items_for_owner(
        changeset_id="cs-empty",
        owner_id="owner-1",
    ) == []
