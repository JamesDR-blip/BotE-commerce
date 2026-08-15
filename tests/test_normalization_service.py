from __future__ import annotations

import pandas as pd
import pytest

from services.normalization_service import NormalizationService


def test_normalize_returns_new_frame_without_mutating_input():
    frame = pd.DataFrame(
        {
            "product_title": ["  Nike   Air   Max  "],
            "color": [" black "],
            "sku": ["AbC-001"],
        }
    )

    original = frame.copy(deep=True)

    service = NormalizationService()

    result = service.normalize(
        frame,
        fields=("product_title", "color"),
    )

    assert result is not frame

    pd.testing.assert_frame_equal(frame, original)

    assert result["product_title"].tolist() == [
        "Nike Air Max"
    ]

    assert result["color"].tolist() == [
        "Black"
    ]

    assert result["sku"].tolist() == [
        "AbC-001"
    ]


def test_normalize_only_requested_fields():
    frame = pd.DataFrame(
        {
            "product_title": ["  Nike   Air   Max  "],
            "color": [" black "],
        }
    )

    service = NormalizationService()

    result = service.normalize(
        frame,
        fields=("color",),
    )

    assert result["color"].tolist() == ["Black"]

    assert result["product_title"].tolist() == [
        "  Nike   Air   Max  "
    ]


def test_normalize_unknown_field_raises():
    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    service = NormalizationService()

    with pytest.raises(ValueError, match="Unknown normalization field"):
        service.normalize(
            frame,
            fields=("does_not_exist",),
        )