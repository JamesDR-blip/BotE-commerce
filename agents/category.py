"""Deterministic category inference agent."""
from __future__ import annotations

import pandas as pd


class CategoryAgent:
    """Infer a supported category from a tabular schema and product titles."""

    def classify(self, frame: pd.DataFrame, choices: list[str], requested: str | None = None) -> str:
        if requested:
            if requested not in choices:
                raise ValueError(f"Unsupported category: {requested}")
            return requested
        columns = {str(column).casefold() for column in frame.columns}
        signals = {
            "Fashion": {"size", "color"},
            "Cosmetics": {"volume", "ingredients"},
            "HomeAppliances": {"power", "dimensions"},
        }
        scores = {category: len(columns & signals.get(category, set())) for category in choices}
        title_column = next((column for column in frame.columns if str(column).casefold() == "product_title"), None)
        if title_column is not None:
            appliance_terms = r"\b(?:fan|air fryer|humidifier|toothbrush|flosser|massager|printer|epilator|trimmer|appliance)\b"
            scores["HomeAppliances"] = scores.get("HomeAppliances", 0) + int(
                frame[title_column].fillna("").astype(str).str.contains(appliance_terms, case=False, regex=True).sum()
            )
        return max(choices, key=lambda category: scores.get(category, 0))
