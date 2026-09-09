import pandas as pd

from domain.studio.profiling import DatasetProfileService


def test_profiles_dataset_structure() -> None:
    frame = pd.DataFrame(
        {
            "sku": ["A", "B", "B", None],
            "price": [10, 20, 20, 30],
            "title": ["Shirt", "Pants", "Pants", "Hat"],
        }
    )

    profile = DatasetProfileService().profile(frame)

    assert profile.row_count == 4
    assert profile.column_count == 3
    assert profile.duplicate_row_count == 1

    sku = profile.columns[0]

    assert sku.name == "sku"
    assert sku.dtype == "object"
    assert sku.null_count == 1
    assert sku.null_ratio == 0.25
    assert sku.unique_count == 3
    assert sku.sample_values == ("A", "B", None)


def test_profile_limits_sample_values() -> None:
    frame = pd.DataFrame(
        {
            "sku": ["A", "B", "C", "D", "E"],
        }
    )

    profile = DatasetProfileService(sample_size=3).profile(frame)

    assert profile.columns[0].sample_values == ("A", "B", "C")

def test_profiles_empty_dataset() -> None:
    frame = pd.DataFrame(
        {
            "sku": pd.Series(dtype="object"),
            "price": pd.Series(dtype="int64"),
        }
    )

    profile = DatasetProfileService().profile(frame)

    assert profile.row_count == 0
    assert profile.column_count == 2
    assert profile.duplicate_row_count == 0

    assert profile.columns[0].null_count == 0
    assert profile.columns[0].null_ratio == 0.0
    assert profile.columns[0].unique_count == 0
    assert profile.columns[0].sample_values == ()


def test_profiles_all_null_column() -> None:
    frame = pd.DataFrame(
        {
            "sku": [None, None, None],
        }
    )

    profile = DatasetProfileService().profile(frame)

    column = profile.columns[0]

    assert column.null_count == 3
    assert column.null_ratio == 1.0
    assert column.unique_count == 1
    assert column.sample_values == (None,)
