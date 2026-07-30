"""Safe, reusable parsing of supported tabular uploads."""
from __future__ import annotations

from io import BytesIO
from pathlib import PurePath

import pandas as pd


class UploadValidationError(ValueError):
    """Raised when an uploaded file is not a safe, supported data file."""


class TabularUploadReader:
    """Parse CSV and Excel uploads without trusting their client-supplied metadata."""

    _SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
    _FORMULA_PREFIXES = ("=", "+", "-", "@")

    def __init__(self, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self._max_bytes = max_bytes

    def read(self, filename: str | None, content: bytes) -> pd.DataFrame:
        safe_name = PurePath(filename or "").name
        extension = PurePath(safe_name).suffix.lower()
        if not safe_name or safe_name != filename or extension not in self._SUPPORTED_EXTENSIONS:
            raise UploadValidationError("Only CSV, XLS, and XLSX uploads are supported")
        if not content:
            raise UploadValidationError("Input file is empty")
        if len(content) > self._max_bytes:
            raise UploadValidationError(f"Input file exceeds the {self._max_bytes}-byte limit")
        try:
            frame = pd.read_csv(BytesIO(content)) if extension == ".csv" else pd.read_excel(BytesIO(content))
        except Exception as exc:  # Parsers expose several implementation-specific error types.
            raise UploadValidationError("Could not parse the uploaded tabular file") from exc
        if frame.empty:
            raise UploadValidationError("Input has no records")
        return self._escape_spreadsheet_formulas(frame)

    def _escape_spreadsheet_formulas(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Prevent uploaded cells from becoming formulas when exported to spreadsheets."""
        sanitized = frame.copy()
        for column in sanitized.select_dtypes(include=["object", "string"]).columns:
            sanitized[column] = sanitized[column].map(self._escape_value)
        return sanitized

    def _escape_value(self, value: object) -> object:
        if isinstance(value, str) and value.startswith(self._FORMULA_PREFIXES):
            return "'" + value
        return value
