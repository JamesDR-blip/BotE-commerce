"""Repository for workflow execution persistence."""

from __future__ import annotations

import json

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import WorkflowExecutionRecord


class WorkflowExecutionRepository:

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions


    def create(
        self,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        status: str = "CREATED",
        inputs: dict | None = None,
        inputs_json: str | None = None,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            if inputs_json is None and inputs is not None:
                inputs_json = json.dumps(inputs)

            record = WorkflowExecutionRecord(
                id=execution_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                status=status,
                inputs_json=inputs_json,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record


    def mark_running(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            record.status = "RUNNING"
            record.started_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(record)

            return record


    def complete(
        self,
        *,
        execution_id: str,
        outputs_json: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            record.status = "COMPLETED"
            record.outputs_json = outputs_json
            record.finished_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(record)

            return record


    def fail(
        self,
        *,
        execution_id: str,
        error: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            record.status = "FAILED"
            record.error = error
            record.finished_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(record)

            return record


    def get(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord | None:

        with self._sessions() as session:

            return session.get(
                WorkflowExecutionRecord,
                execution_id,
            )


    def list_by_workflow(
        self,
        workflow_id: str,
    ) -> list[WorkflowExecutionRecord]:

        with self._sessions() as session:

            return list(
                session.scalars(
                    select(
                        WorkflowExecutionRecord
                    )
                    .where(
                        WorkflowExecutionRecord.workflow_id
                        == workflow_id
                    )
                    .order_by(
                        WorkflowExecutionRecord.created_at
                    )
                )
            )
    def _get_mutable(
        self,
        session: Session,
        execution_id: str,
    ) -> WorkflowExecutionRecord:
        record = session.get(
            WorkflowExecutionRecord,
            execution_id,
        )

        if record is None:
            raise ValueError(
                f"Workflow execution not found: {execution_id}"
            )

        if record.status in {"COMPLETED", "FAILED"}:
            raise ValueError(
                f"Workflow execution is terminal: "
                f"{execution_id} ({record.status})"
            )

        return record