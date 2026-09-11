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


class FakeStorage:
    def __init__(self):
        self.files = {}

    def save(self, *, storage_key, content):
        self.files[storage_key] = content
        return storage_key

    def open(self, *, storage_key):
        from io import BytesIO

        return BytesIO(self.files[storage_key])


def test_ingest_persists_dataset_metadata():
    repository = FakeRepository()

    from infrastructure.upload.streaming_reader import StreamingTabularReader

    service = DatasetIngestionService(
        reader=FakeReader(),
        streaming_reader=StreamingTabularReader(
            max_bytes=1024 * 1024,
            chunk_size=10_000,
        ),
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
def test_ingest_persists_source_and_storage_reference():
    repository = FakeRepository()
    storage = FakeStorage()

    from infrastructure.upload.streaming_reader import StreamingTabularReader

    service = DatasetIngestionService(
        reader=FakeReader(),
        streaming_reader=StreamingTabularReader(
            max_bytes=1024 * 1024,
            chunk_size=10_000,
        ),
        datasets=repository,
        profiler=DatasetProfileService(),
        storage=storage,
    )

    content = b"title,price\nShirt,100\nPants,200\n"

    service.ingest(
        dataset_id="d-2",
        project_id="p-1",
        name="catalog",
        filename="products.csv",
        content=content,
        source_type="upload",
    )

    assert repository.kwargs["storage_key"] == "d-2.csv"
    assert "d-2.csv" in storage.files

    with storage.open(storage_key=repository.kwargs["storage_key"]) as source:
        assert source.read() == content

def test_streaming_ingestion_persists_exact_profile(
    tmp_path,
) -> None:
    from io import BytesIO

    from infrastructure.upload.streaming_reader import StreamingTabularReader

    class FakeStorage:
        def __init__(self) -> None:
            self.saved = {}
            self.save_stream_calls = []

        def save(self, *, storage_key: str, content: bytes) -> str:
            self.saved[storage_key] = content
            return storage_key

        def save_stream(self, *, storage_key: str, source) -> str:
            self.save_stream_calls.append(storage_key)
            self.saved[storage_key] = source.read()
            return storage_key

        def open(self, *, storage_key: str):
            return BytesIO(self.saved[storage_key])

    class FakeDatasets:
        def __init__(self) -> None:
            self.created = None

        def create(self, **kwargs):
            self.created = kwargs
            return kwargs

    content = (
        b"id,value\n"
        b"1,100\n"
        b"2,200\n"
        b"3,unknown\n"
        b"4,400\n"
    )

    datasets = FakeDatasets()
    storage = FakeStorage()


    streaming_reader = StreamingTabularReader(
        max_bytes=1024 * 1024,
        chunk_size=2,
    )

    service = DatasetIngestionService(
        reader=None,
        streaming_reader=streaming_reader,
        datasets=datasets,
        profiler=DatasetProfileService(),
        storage=storage,
    )

    expected_hash = hashlib.sha256(content).hexdigest()

    result = service.ingest_streaming(
        dataset_id="dataset-1",
        project_id="project-1",
        name="Test dataset",
        filename="test.csv",
        source=BytesIO(content),
    )

    assert result["row_count"] == 4
    assert result["column_count"] == 2

    profile = result["metadata"]["profile"]

    assert profile["row_count"] == 4
    assert profile["column_count"] == 2
    assert profile["columns"][0]["dtype"] == "int64"
    assert profile["columns"][1]["dtype"] == "object"

    assert result["size_bytes"] == len(content)
    assert result["content_hash"] == expected_hash
    assert result["storage_key"] == "dataset-1.csv"
    assert storage.save_stream_calls == ["dataset-1.csv"]
    assert storage.saved["dataset-1.csv"] == content
