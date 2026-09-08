"""Backward-compatible import for tabular upload infrastructure."""
from infrastructure.upload.tabular_reader import (
    TabularUploadReader,
    UploadValidationError,
)

__all__ = ["TabularUploadReader", "UploadValidationError"]
