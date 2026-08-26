"""Repository for workflow persistence."""

from __future__ import annotations

from typing import Callable
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    WorkflowRecord,
    WorkflowVersionRecord,
)


class WorkflowRepository:

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions


    def create(
        self,
        *,
        workflow_id: str,
        project_id: str,
        name: str,
        version: str,
        plan_json: str,
    ) -> WorkflowRecord:

        with self._sessions() as session:

            workflow = WorkflowRecord(
                id=workflow_id,
                project_id=project_id,
                name=name,
                active_version=version,
                status="DRAFT",
            )

            session.add(workflow)

            workflow_version = WorkflowVersionRecord(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                version=version,
                plan_json=plan_json,
            )

            session.add(workflow_version)

            session.commit()
            session.refresh(workflow)

            return workflow


    def get(
        self,
        workflow_id: str,
    ) -> WorkflowRecord | None:

        with self._sessions() as session:
            return session.get(
                WorkflowRecord,
                workflow_id,
            )
        
    def get_version(
        self,
        workflow_id: str,
        version: str,
    ) -> WorkflowVersionRecord | None:

        with self._sessions() as session:
            return session.scalar(
                select(WorkflowVersionRecord).where(
                    WorkflowVersionRecord.workflow_id == workflow_id,
                    WorkflowVersionRecord.version == version,
                )
            )

    def list_versions(
        self,
        workflow_id: str,
    ) -> list[WorkflowVersionRecord]:

        with self._sessions() as session:
            return list(
                session.scalars(
                    select(WorkflowVersionRecord)
                    .where(
                        WorkflowVersionRecord.workflow_id == workflow_id
                    )
                    .order_by(
                        WorkflowVersionRecord.created_at
                    )
                )
            )

    def create_version(
        self,
        *,
        workflow_id: str,
        version: str,
        plan_json: str,
    ) -> WorkflowVersionRecord:

        with self._sessions() as session:

            existing = session.scalar(
                select(WorkflowVersionRecord).where(
                    WorkflowVersionRecord.workflow_id == workflow_id,
                    WorkflowVersionRecord.version == version,
                )
            )

            if existing is not None:
                raise ValueError(
                    f"Workflow version already exists: "
                    f"{workflow_id}@{version}"
                )

            record = WorkflowVersionRecord(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                version=version,
                plan_json=plan_json,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def get_active_version(
        self,
        workflow_id: str,
    ) -> WorkflowVersionRecord | None:

        with self._sessions() as session:

            workflow = session.get(
                WorkflowRecord,
                workflow_id,
            )

            if workflow is None:
                return None

            return session.scalar(
                select(WorkflowVersionRecord)
                .where(
                    WorkflowVersionRecord.workflow_id == workflow_id,
                    WorkflowVersionRecord.version == workflow.active_version,
                )
            )

    def activate_version(
        self,
        workflow_id: str,
        version: str,
    ) -> WorkflowRecord:

        with self._sessions() as session:

            workflow = session.get(
                WorkflowRecord,
                workflow_id,
            )

            if workflow is None:
                raise ValueError(
                    f"Workflow not found: {workflow_id}"
                )

            version_record = session.scalar(
                select(WorkflowVersionRecord)
                .where(
                    WorkflowVersionRecord.workflow_id == workflow_id,
                    WorkflowVersionRecord.version == version,
                )
            )

            if version_record is None:
                raise ValueError(
                    f"Workflow version not found: {version}"
                )

            workflow.active_version = version

            session.commit()
            session.refresh(workflow)

            return workflow

    def list_by_project(
        self,
        project_id: str,
    ) -> list[WorkflowRecord]:

        with self._sessions() as session:

            return list(
                session.scalars(
                    select(WorkflowRecord)
                    .where(
                        WorkflowRecord.project_id
                        == project_id
                    )
                )
            )