from io import BytesIO

import pandas as pd
import pytest
from openpyxl import Workbook

from infrastructure.upload.streaming_reader import StreamingTabularReader
from infrastructure.upload.tabular_reader import UploadValidationError


def test_streams_csv_in_bounded_chunks() -> None:
    content = (
        b"name,price\n"
        b"shirt,10\n"
        b"pants,20\n"
        b"shoes,30\n"
        b"hat,40\n"
        b"coat,50\n"
    )

    chunks = list(
        StreamingTabularReader(
            max_bytes=1024,
            chunk_size=2,
        ).stream("products.csv", content)
    )

    assert len(chunks) == 3
    assert [len(chunk) for chunk in chunks] == [2, 2, 1]
    assert pd.concat(chunks, ignore_index=True).to_dict("records") == [
        {"name": "shirt", "price": 10},
        {"name": "pants", "price": 20},
        {"name": "shoes", "price": 30},
        {"name": "hat", "price": 40},
        {"name": "coat", "price": 50},
    ]


def test_streams_xlsx_in_bounded_chunks() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["name", "price"])

    for index in range(5):
        worksheet.append([f"product-{index}", index])

    buffer = BytesIO()
    workbook.save(buffer)

    chunks = list(
        StreamingTabularReader(
            max_bytes=1024 * 1024,
            chunk_size=2,
        ).stream("products.xlsx", buffer.getvalue())
    )

    assert len(chunks) == 3
    assert [len(chunk) for chunk in chunks] == [2, 2, 1]


def test_streaming_reader_escapes_formulas() -> None:
    content = b"name,price\n=SUM(A1),10\n@user,20\n"

    chunks = list(
        StreamingTabularReader(
            max_bytes=1024,
            chunk_size=1,
        ).stream("products.csv", content)
    )

    assert chunks[0].iloc[0]["name"] == "'=SUM(A1)"
    assert chunks[1].iloc[0]["name"] == "'@user"


def test_streaming_reader_rejects_unsupported_extension() -> None:
    with pytest.raises(
        UploadValidationError,
        match="Only CSV and XLSX",
    ):
        list(
            StreamingTabularReader(
                max_bytes=1024,
                chunk_size=2,
            ).stream("products.xls", b"data")
        )


@pytest.mark.parametrize(
    "chunk_size",
    [0, -1],
)
def test_streaming_reader_rejects_invalid_chunk_size(
    chunk_size: int,
) -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        StreamingTabularReader(
            max_bytes=1024,
            chunk_size=chunk_size,
        )


def test_streaming_reader_rejects_empty_csv() -> None:
    with pytest.raises(
        UploadValidationError,
        match="Input file is empty",
    ):
        list(
            StreamingTabularReader(
                max_bytes=1024,
                chunk_size=2,
            ).stream("products.csv", b"")
        )

