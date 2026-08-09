"""Observability helpers for LangGraph workflow nodes."""
from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Callable

from .state import WorkflowState


logger = logging.getLogger(__name__)


def observe_node(
    name: str,
    node: Callable[[WorkflowState], dict[str, Any]],
) -> Callable[[WorkflowState], dict[str, Any]]:
    """Wrap a workflow node with structured lifecycle logging."""

    def observed(state: WorkflowState) -> dict[str, Any]:
        execution_id = state.get("execution_id", "unknown")
        started_at = perf_counter()

        logger.info(
            "node_started",
            extra={
                "event": "node_started",
                "execution_id": execution_id,
                "node": name,
            },
        )

        try:
            result = node(state)

            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.info(
                "node_completed",
                extra={
                    "event": "node_completed",
                    "execution_id": execution_id,
                    "node": name,
                    "duration_ms": duration_ms,
                },
            )

            return result

        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "node_failed",
                extra={
                    "event": "node_failed",
                    "execution_id": execution_id,
                    "node": name,
                    "duration_ms": duration_ms,
                },
            )
            raise

    return observed


__all__ = ["observe_node"]