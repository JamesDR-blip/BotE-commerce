import pandas as pd
import pytest

from application.datasets.artifact_materializer import (
    DatasetArtifactMaterializer,
)
from infrastructure.storage.dataset_storage import DatasetStorage


def test_materialize_csv_creates_unique_immutable_artifact(tmp_path):
    storage = DatasetStorage(tmp_path)
    materializer = DatasetArtifactMaterializer(storage=storage)

    frame = pd.DataFrame(
        [
            {"id": 1, "title": "Shirt"},
            {"id": 2, "title": "Pants"},
        ]
    )

    storage_key, content_hash = materializer.materialize(
        frame=frame,
        file_format="csv",
        changeset_id="changeset-1",
    )

    assert storage_key == (
        "changesets/changeset-1/after.csv"
    )
    assert len(content_hash) == 64

    with storage.open(storage_key=storage_key) as source:
        content = source.read()

    assert content == (
        b"id,title\n"
        b"1,Shirt\n"
        b"2,Pants\n"
    )


def test_materialize_csv_round_trips_dataframe(tmp_path):
    storage = DatasetStorage(tmp_path)
    materializer = DatasetArtifactMaterializer(storage=storage)

    frame = pd.DataFrame(
        [
            {"id": 1, "price": 100},
            {"id": 2, "price": 200},
        ]
    )

    storage_key, _ = materializer.materialize(
        frame=frame,
        file_format="csv",
        changeset_id="changeset-roundtrip",
    )

    with storage.open(storage_key=storage_key) as source:
        restored = pd.read_csv(source)

    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_materialize_xlsx_round_trips_dataframe(tmp_path):
    storage = DatasetStorage(tmp_path)
    materializer = DatasetArtifactMaterializer(storage=storage)

    frame = pd.DataFrame(
        [
            {"id": 1, "title": "Shirt"},
            {"id": 2, "title": "Pants"},
        ]
    )

    storage_key, content_hash = materializer.materialize(
        frame=frame,
        file_format="xlsx",
        changeset_id="changeset-xlsx",
    )

    assert storage_key == (
        "changesets/changeset-xlsx/after.xlsx"
    )
    assert len(content_hash) == 64

    with storage.open(storage_key=storage_key) as source:
        restored = pd.read_excel(source)

    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_materialize_rejects_unsupported_format(tmp_path):
    storage = DatasetStorage(tmp_path)
    materializer = DatasetArtifactMaterializer(storage=storage)

    with pytest.raises(
        ValueError,
        match="Unsupported dataset artifact format",
    ):
        materializer.materialize(
            frame=pd.DataFrame({"id": [1]}),
            file_format="xls",
            changeset_id="changeset-xls",
        )


def test_materialize_verifies_persisted_hash(tmp_path):
    storage = DatasetStorage(tmp_path)
    materializer = DatasetArtifactMaterializer(storage=storage)

    frame = pd.DataFrame({"id": [1, 2, 3]})

    storage_key, content_hash = materializer.materialize(
        frame=frame,
        file_format="csv",
        changeset_id="changeset-hash",
    )

    import hashlib

    with storage.open(storage_key=storage_key) as source:
        persisted_hash = hashlib.sha256(
            source.read()
        ).hexdigest()

    assert persisted_hash == content_hash
