"""Backward-compatible imports for HTTP response contracts.

HTTP schemas now live in :mod:`schemas.responses`.
"""
from schemas.responses import (
    CapabilityTraceResponse,
    ExecutionDetailResponse,
    ExecutionHistoryItem,
    ExtractionRecordResponse,
    ExtractionResponse,
    HistoryResponse,
    MappingResponse,
    TabularPreviewResponse,
    UploadResponse,
    ValidationResponse,
)

__all__ = [
    "CapabilityTraceResponse",
    "ExecutionDetailResponse",
    "ExecutionHistoryItem",
    "ExtractionRecordResponse",
    "ExtractionResponse",
    "HistoryResponse",
    "MappingResponse",
    "TabularPreviewResponse",
    "UploadResponse",
    "ValidationResponse",
]