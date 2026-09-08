"""Backward-compatible import for the workflow history application service."""
from application.workflows.history_service import WorkflowHistoryService

__all__ = ["WorkflowHistoryService"]
