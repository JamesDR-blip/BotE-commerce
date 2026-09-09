import hashlib

from application.datasets.dataset_ingestion import DatasetIngestionService
from domain.studio.profiling import DatasetProfileService


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
        profiler=DatasetProfileService(),
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

    assert repository.kwargs["dataset_id"] == "d-1"
    assert repository.kwargs["project_id"] == "p-1"
    assert repository.kwargs["name"] == "catalog"
    assert repository.kwargs["source_type"] == "upload"
    assert repository.kwargs["filename"] == "products.csv"
    assert repository.kwargs["file_format"] == "csv"
    assert repository.kwargs["size_bytes"] == len(content)
    assert repository.kwargs["content_hash"] == expected_hash
    assert repository.kwargs["row_count"] == 2
    assert repository.kwargs["column_count"] == 2
    assert repository.kwargs["status"] == "READY"

    profile = repository.kwargs["metadata"]["profile"]

    assert profile["row_count"] == 2
    assert profile["column_count"] == 2
    assert len(profile["columns"]) == 2

    assert result == repository.kwargs

