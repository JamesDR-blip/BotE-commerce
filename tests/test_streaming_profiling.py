import pandas as pd

from domain.studio.profiling import DatasetProfileService
from application.datasets.streaming_profiling import (
    StreamingProfileAccumulator,
)


def test_streaming_profile_matches_batch_profile() -> None:
    frame = pd.DataFrame(
        {
            "sku": ["A", "B", "B", None, "C", "A"],
            "price": [10, 20, 20, 30, None, 10],
            "title": ["Shirt", "Pants", "Pants", "Hat", "Coat", "Shirt"],
        }
    )

    batch_profile = DatasetProfileService().profile(frame)

    accumulator = StreamingProfileAccumulator(sample_size=5)

    accumulator.update(frame.iloc[:2])
    accumulator.update(frame.iloc[2:4])
    accumulator.update(frame.iloc[4:])

    streaming_profile = accumulator.finalize()

    assert streaming_profile.row_count == batch_profile.row_count
    assert (
        streaming_profile.column_count
        == batch_profile.column_count
    )
    assert (
        streaming_profile.duplicate_row_count
        == batch_profile.duplicate_row_count
    )

    assert len(streaming_profile.columns) == len(batch_profile.columns)

    for actual, expected in zip(
        streaming_profile.columns,
        batch_profile.columns,
    ):
        assert actual.name == expected.name
        assert actual.dtype == expected.dtype
        assert actual.null_count == expected.null_count
        assert actual.null_ratio == expected.null_ratio
        assert actual.unique_count == expected.unique_count
        assert len(actual.sample_values) == len(expected.sample_values)

        for actual_value, expected_value in zip(
            actual.sample_values,
            expected.sample_values,
        ):
            if pd.isna(actual_value) and pd.isna(expected_value):
                continue
            assert actual_value == expected_value


def test_streaming_profile_preserves_sample_order_across_chunks() -> None:
    frame = pd.DataFrame(
        {
            "sku": ["A", "B", "C", "D", "E"],
        }
    )

    accumulator = StreamingProfileAccumulator(sample_size=3)

    accumulator.update(frame.iloc[:2])
    accumulator.update(frame.iloc[2:])

    profile = accumulator.finalize()

    assert profile.columns[0].sample_values == ("A", "B", "C")


def test_streaming_profile_counts_cross_chunk_duplicates() -> None:
    first = pd.DataFrame(
        {
            "sku": ["A", "B"],
            "price": [10, 20],
        }
    )
    second = pd.DataFrame(
        {
            "sku": ["B", "C"],
            "price": [20, 30],
        }
    )

    accumulator = StreamingProfileAccumulator()

    accumulator.update(first)
    accumulator.update(second)

    profile = accumulator.finalize()

    assert profile.row_count == 4
    assert profile.duplicate_row_count == 1
    assert profile.columns[0].unique_count == 3
    assert profile.columns[1].unique_count == 3


def test_streaming_profile_handles_all_null_values() -> None:
    first = pd.DataFrame({"sku": [None, None]})
    second = pd.DataFrame({"sku": [None]})

    accumulator = StreamingProfileAccumulator()

    accumulator.update(first)
    accumulator.update(second)

    profile = accumulator.finalize()

    assert profile.row_count == 3
    assert profile.duplicate_row_count == 2
    assert profile.columns[0].null_count == 3
    assert profile.columns[0].null_ratio == 1.0
    assert profile.columns[0].unique_count == 1
    assert profile.columns[0].sample_values == (None,)


def test_streaming_profile_rejects_inconsistent_columns() -> None:
    accumulator = StreamingProfileAccumulator()

    accumulator.update(pd.DataFrame({"sku": ["A"], "price": [10]}))

    try:
        accumulator.update(pd.DataFrame({"sku": ["B"]}))
    except ValueError as exc:
        assert "columns" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

def test_streaming_profile_preserves_mixed_numeric_duplicate_semantics() -> None:
    frame = pd.DataFrame(
        {
            "integer_value": pd.Series([1, 2, 1, 3], dtype="int64"),
            "float_value": pd.Series([1.5, 2.5, 1.5, 3.5], dtype="float64"),
        }
    )

    batch_profile = DatasetProfileService().profile(frame)

    accumulator = StreamingProfileAccumulator(sample_size=5)
    accumulator.update(frame.iloc[:2])
    accumulator.update(frame.iloc[2:])

    streaming_profile = accumulator.finalize()

    assert streaming_profile.row_count == batch_profile.row_count
    assert (
        streaming_profile.duplicate_row_count
        == batch_profile.duplicate_row_count
    )
    assert streaming_profile.columns == batch_profile.columns


def test_streaming_profile_preserves_column_dtypes_across_chunks() -> None:
    frame = pd.DataFrame(
        {
            "value": [1, 2, 3, 4],
            "label": ["a", "b", "c", "d"],
        }
    )

    batch_profile = DatasetProfileService().profile(frame)

    accumulator = StreamingProfileAccumulator(sample_size=5)
    accumulator.update(frame.iloc[:1])
    accumulator.update(frame.iloc[1:])

    streaming_profile = accumulator.finalize()

    assert [
        column.dtype for column in streaming_profile.columns
    ] == [
        column.dtype for column in batch_profile.columns
    ]

def test_streaming_profile_reconciles_dtype_across_chunks() -> None:
    frame = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": [100, 200, "unknown", 400],
        }
    )

    batch_profile = DatasetProfileService().profile(frame)

    accumulator = StreamingProfileAccumulator(sample_size=5)
    accumulator.update(
        pd.DataFrame(
            {
                "id": pd.Series([1, 2], dtype="int64"),
                "value": pd.Series([100, 200], dtype="int64"),
            }
        )
    )
    accumulator.update(
        pd.DataFrame(
            {
                "id": pd.Series([3, 4], dtype="int64"),
                "value": pd.Series(["unknown", 400], dtype="object"),
            }
        )
    )

    streaming_profile = accumulator.finalize()

    assert streaming_profile.columns[0].dtype == "int64"
    assert streaming_profile.columns[1].dtype == "object"
    assert streaming_profile.columns == batch_profile.columns


def test_streaming_profile_reconciles_integer_and_float_dtypes() -> None:
    frame = pd.DataFrame(
        {
            "value": [1, 2, 3.5, 4.5],
        }
    )

    batch_profile = DatasetProfileService().profile(frame)

    accumulator = StreamingProfileAccumulator(sample_size=5)
    accumulator.update(
        pd.DataFrame(
            {"value": pd.Series([1, 2], dtype="int64")}
        )
    )
    accumulator.update(
        pd.DataFrame(
            {"value": pd.Series([3.5, 4.5], dtype="float64")}
        )
    )

    streaming_profile = accumulator.finalize()

    assert streaming_profile.columns[0].dtype == "float64"
    assert streaming_profile.columns == batch_profile.columns
