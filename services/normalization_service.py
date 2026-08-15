"""Deterministic, non-mutating normalization for ecommerce tabular data."""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd


class NormalizationService:
    """Normalize selected ecommerce fields without mutating the input frame."""

    _SUPPORTED_FIELDS = {
        "product_title",
        "color",
    }

    def normalize(
        self,
        frame: pd.DataFrame,
        fields: Iterable[str],
    ) -> pd.DataFrame:
        """Return a normalized copy of the input DataFrame."""
        unknown_fields = [
            field
            for field in fields
            if field not in self._SUPPORTED_FIELDS
        ]

        if unknown_fields:
            raise ValueError(
                "Unknown normalization field: "
                + ", ".join(unknown_fields)
            )

        result = frame.copy(deep=True)

        for field in fields:
            if field not in result.columns:
                raise ValueError(
                    f"Normalization field not present in frame: {field}"
                )

            if field == "product_title":
                result[field] = (
                    result[field]
                    .fillna("")
                    .astype(str)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                )

            elif field == "color":
                result[field] = (
                    result[field]
                    .fillna("")
                    .astype(str)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                    .str.casefold()
                    .replace(
                        {
                            "black": "Black",
                            "white": "White",
                            "pink": "Pink",
                            "red": "Red",
                            "blue": "Blue",
                            "green": "Green",
                            "purple": "Purple",
                            "silver": "Silver",
                            "gold": "Gold",
                            "grey": "Grey",
                            "gray": "Grey",
                            "colored": "Colored",
                        }
                    )
                )

        return result