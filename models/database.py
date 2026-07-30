"""Backward-compatible imports for persistence models.

Persistence models now live in :mod:`database.models`.
"""
from database.models import Base, ExecutionRecord, ReportRecord, ValidationLogRecord, make_session_factory

__all__ = ["Base", "ExecutionRecord", "ReportRecord", "ValidationLogRecord", "make_session_factory"]
