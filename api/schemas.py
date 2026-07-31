"""Backward-compatible imports for HTTP response contracts.

HTTP schemas now live in :mod:`schemas.responses`.
"""
from schemas.responses import (
    ExecutionHistoryItem,
    ExtractionRecordResponse,
    ExtractionResponse,
    HistoryResponse,
    MappingResponse,
    TabularPreviewResponse,
    UploadResponse,
    ValidationResponse,
)

__all__ = ["ExecutionHistoryItem", "ExtractionRecordResponse", "ExtractionResponse", "HistoryResponse", "MappingResponse", "TabularPreviewResponse", "UploadResponse", "ValidationResponse"]
