"""Repository for workflow execution persistence."""

from __future__ import annotations

import json

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select, update
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
        dataset_id: str | None = None,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            if inputs_json is None and inputs is not None:
                inputs_json = json.dumps(inputs)

            record = WorkflowExecutionRecord(
                id=execution_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                dataset_id=dataset_id,
                status=status,
                inputs_json=inputs_json,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def mark_pending_approval(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            if record.status not in {"CREATED", "QUEUED"}:
                raise ValueError(
                    "Workflow execution cannot enter approval state: "
                    f"{execution_id} ({record.status})"
                )

            record.status = "PENDING_APPROVAL"

            session.commit()
            session.refresh(record)

            return record

    def release_to_queue(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            if record.status != "PENDING_APPROVAL":
                raise ValueError(
                    "Workflow execution is not pending approval: "
                    f"{execution_id} ({record.status})"
                )

            record.status = "QUEUED"

            session.commit()
            session.refresh(record)

            return record

    def cancel(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            record = self._get_mutable(
                session,
                execution_id,
            )

            if record.status != "PENDING_APPROVAL":
                raise ValueError(
                    "Only pending approval executions can be cancelled: "
                    f"{execution_id} ({record.status})"
                )

            record.status = "CANCELLED"
            record.finished_at = datetime.now(timezone.utc)

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

            if record.status not in {"CREATED", "QUEUED"}:
                raise ValueError(
                    "Workflow execution cannot start running: "
                    f"{execution_id} ({record.status})"
                )

            record.status = "RUNNING"
            record.started_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(record)

            return record

    def claim_running(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord | None:
        """
        Atomically claim a queued execution for worker execution.

        Returns the running record when this worker successfully claims it.
        Returns None when another worker already claimed it or the execution
        is no longer queued.
        """

        with self._sessions() as session:

            now = datetime.now(timezone.utc)

            result = session.execute(
                update(WorkflowExecutionRecord)
                .where(
                    WorkflowExecutionRecord.id == execution_id,
                    WorkflowExecutionRecord.status == "QUEUED",
                )
                .values(
                    status="RUNNING",
                    started_at=now,
                )
            )

            if result.rowcount != 1:
                session.rollback()
                return None

            session.commit()

            record = session.get(
                WorkflowExecutionRecord,
                execution_id,
            )

            if record is None:
                return None

            return record

    def complete(
        self,
        *,
        execution_id: str,
        outputs_json: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            result = session.execute(
                update(WorkflowExecutionRecord)
                .where(
                    WorkflowExecutionRecord.id == execution_id,
                    WorkflowExecutionRecord.status.not_in(
                        {"COMPLETED", "FAILED", "CANCELLED"}
                    ),
                )
                .values(
                    status="COMPLETED",
                    outputs_json=outputs_json,
                    finished_at=datetime.now(timezone.utc),
                )
            )

            if result.rowcount != 1:
                session.rollback()
                record = session.get(WorkflowExecutionRecord, execution_id)
                if record is None:
                    raise ValueError(
                        f"Workflow execution not found: {execution_id}"
                    )
                raise ValueError(
                    "Workflow execution is already terminal: "
                    f"{execution_id} ({record.status})"
                )

            session.commit()
            record = session.get(WorkflowExecutionRecord, execution_id)

            return record

    def get_in_transaction(
        self,
        session: Session,
        execution_id: str,
    ) -> WorkflowExecutionRecord | None:
        return session.get(
            WorkflowExecutionRecord,
            execution_id,
        )

    def complete_after_approval_in_transaction(
        self,
        session: Session,
        *,
        execution_id: str,
        outputs_json: str,
    ) -> WorkflowExecutionRecord:
        record = session.get(
            WorkflowExecutionRecord,
            execution_id,
        )

        if record is None:
            raise ValueError(
                f"Workflow execution not found: {execution_id}"
            )

        if record.status != "PENDING_APPROVAL":
            raise ValueError(
                "Workflow execution is not pending approval: "
                f"{execution_id} ({record.status})"
            )

        record.status = "COMPLETED"
        record.outputs_json = outputs_json
        record.finished_at = datetime.now(timezone.utc)

        session.flush()

        return record

    def fail(
        self,
        *,
        execution_id: str,
        error: str,
    ) -> WorkflowExecutionRecord:

        with self._sessions() as session:

            result = session.execute(
                update(WorkflowExecutionRecord)
                .where(
                    WorkflowExecutionRecord.id == execution_id,
                    WorkflowExecutionRecord.status.not_in(
                        {"COMPLETED", "FAILED", "CANCELLED"}
                    ),
                )
                .values(
                    status="FAILED",
                    error=error,
                    finished_at=datetime.now(timezone.utc),
                )
            )

            if result.rowcount != 1:
                session.rollback()
                record = session.get(WorkflowExecutionRecord, execution_id)
                if record is None:
                    raise ValueError(
                        f"Workflow execution not found: {execution_id}"
                    )
                raise ValueError(
                    "Workflow execution is already terminal: "
                    f"{execution_id} ({record.status})"
                )

            session.commit()
            record = session.get(WorkflowExecutionRecord, execution_id)

            return record

    def fail_if_running(
        self,
        *,
        execution_id: str,
        error: str,
    ) -> WorkflowExecutionRecord | None:
        """Persist crash recovery only while an execution is still RUNNING."""
        with self._sessions() as session:
            result = session.execute(
                update(WorkflowExecutionRecord)
                .where(
                    WorkflowExecutionRecord.id == execution_id,
                    WorkflowExecutionRecord.status == "RUNNING",
                )
                .values(
                    status="FAILED",
                    error=error,
                    finished_at=datetime.now(timezone.utc),
                )
            )

            if result.rowcount != 1:
                session.rollback()
                return None

            session.commit()
            return session.get(WorkflowExecutionRecord, execution_id)

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
