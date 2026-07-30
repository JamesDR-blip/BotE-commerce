"""Backward-compatible imports for domain value objects.

Domain models now live in :mod:`domain.models`.
"""
from domain.models import ExecutionSummary, ValidationIssue, ValidationResult

__all__ = ["ExecutionSummary", "ValidationIssue", "ValidationResult"]
