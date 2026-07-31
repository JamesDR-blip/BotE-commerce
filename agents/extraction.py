"""Read-only agent for batch product attribute extraction."""
from __future__ import annotations

import pandas as pd

from extractors.base import ExtractedAttributes, ProductExtractor


class ExtractionAgent:
    """Apply the configured extractor to product-title-like columns."""

    _TITLE_COLUMNS = ("product_title", "title", "name")

    def __init__(self, extractor: ProductExtractor) -> None:
        self._extractor = extractor

    def extract(self, frame: pd.DataFrame) -> list[ExtractedAttributes]:
        title_column = next((column for column in frame.columns if str(column).casefold() in self._TITLE_COLUMNS), None)
        if title_column is None:
            return []
        return [self._extractor.extract(value) for value in frame[title_column]]
