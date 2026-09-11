from io import BytesIO

from infrastructure.storage.dataset_storage import DatasetStorage


def test_save_stream_persists_binary_source(tmp_path):
    storage = DatasetStorage(tmp_path)
    content = b"row,value\n1,100\n2,200\n"

    result = storage.save_stream(
        storage_key="dataset-1.csv",
        source=BytesIO(content),
    )

    assert result == "dataset-1.csv"

    with storage.open(storage_key="dataset-1.csv") as source:
        assert source.read() == content


def test_save_stream_does_not_read_entire_source_at_once(tmp_path):
    storage = DatasetStorage(tmp_path)

    class ChunkedSource(BytesIO):
        def read(self, size=-1):
            if size == -1:
                raise AssertionError(
                    "save_stream must not read the entire source"
                )
            return super().read(size)

    content = b"x" * 200_000

    result = storage.save_stream(
        storage_key="dataset-large.csv",
        source=ChunkedSource(content),
    )

    assert result == "dataset-large.csv"

    with storage.open(storage_key="dataset-large.csv") as source:
        assert source.read() == content


def test_save_stream_rejects_invalid_storage_key(tmp_path):
    storage = DatasetStorage(tmp_path)

    try:
        storage.save_stream(
            storage_key="../escape.csv",
            source=BytesIO(b"unsafe"),
        )
    except ValueError as exc:
        assert str(exc) == "Invalid dataset storage key"
    else:
        raise AssertionError("Expected ValueError")