import pandas as pd
import pytest

from services.upload_reader import TabularUploadReader, UploadValidationError


def test_reads_csv_and_escapes_spreadsheet_formulas() -> None:
    frame = TabularUploadReader(1024).read("products.csv", b"title,price\n=2+2,100\n")
    assert frame.to_dict("records") == [{"title": "'=2+2", "price": 100}]


@pytest.mark.parametrize("filename", ["products.pdf", "../products.csv", None])
def test_rejects_unsupported_or_unsafe_filenames(filename: str | None) -> None:
    with pytest.raises(UploadValidationError):
        TabularUploadReader(1024).read(filename, b"name\nshirt\n")


def test_rejects_oversized_upload() -> None:
    with pytest.raises(UploadValidationError, match="exceeds"):
        TabularUploadReader(3).read("products.csv", b"name\nshirt\n")
