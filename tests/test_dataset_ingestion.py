import hashlib

from services.dataset_ingestion import DatasetIngestionService


class FakeReader:
    def read(self, filename, content):
        import pandas as pd

        return pd.DataFrame(
            [
                {"title": "Shirt", "price": 100},
                {"title": "Pants", "price": 200},
            ]
        )


class FakeRepository:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return kwargs


def test_ingest_persists_dataset_metadata():
    repository = FakeRepository()

    service = DatasetIngestionService(
        reader=FakeReader(),
        datasets=repository,
    )

    content = b"title,price\nShirt,100\nPants,200\n"

    result = service.ingest(
        dataset_id="d-1",
        project_id="p-1",
        name="catalog",
        filename="products.csv",
        content=content,
        source_type="upload",
    )

    expected_hash = hashlib.sha256(content).hexdigest()

    assert repository.kwargs == {
        "dataset_id": "d-1",
        "project_id": "p-1",
        "name": "catalog",
        "source_type": "upload",
        "metadata": {},
        "filename": "products.csv",
        "file_format": "csv",
        "size_bytes": len(content),
        "content_hash": expected_hash,
        "row_count": 2,
        "column_count": 2,
        "status": "READY",
    }

    assert result == repository.kwargs