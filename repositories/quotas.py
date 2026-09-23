"""Persistence repository for organization quotas."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import (
    DatasetRecord,
    OrganizationQuotaRecord,
    ProjectRecord,
    WorkflowExecutionRecord,
    WorkflowRecord,
    WorkspaceRecord,
)
from domain.quota import QuotaDimension


class QuotaRepository:
    """Read/write boundary for organization quotas and usage."""

    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    def get_quota(
        self,
        *,
        organization_id: str,
        dimension: QuotaDimension,
    ) -> OrganizationQuotaRecord | None:
        with self._sessions() as session:
            statement = select(OrganizationQuotaRecord).where(
                OrganizationQuotaRecord.organization_id == organization_id,
                OrganizationQuotaRecord.dimension == dimension.value,
            )
            return session.scalar(statement)

    def set_quota(
        self,
        *,
        quota_id: str,
        organization_id: str,
        dimension: QuotaDimension,
        limit: int,
    ) -> OrganizationQuotaRecord:
        with self._sessions() as session:
            statement = select(OrganizationQuotaRecord).where(
                OrganizationQuotaRecord.organization_id == organization_id,
                OrganizationQuotaRecord.dimension == dimension.value,
            )
            record = session.scalar(statement)

            if record is None:
                record = OrganizationQuotaRecord(
                    id=quota_id,
                    organization_id=organization_id,
                    dimension=dimension.value,
                    limit=limit,
                )
                session.add(record)
            else:
                record.limit = limit

            session.commit()
            session.refresh(record)
            return record
    def get_usage(
        self,
        *,
        organization_id: str,
        dimension: QuotaDimension,
    ) -> int:
        with self._sessions() as session:
            if dimension is QuotaDimension.STORAGE_BYTES:
                statement = (
                    select(func.coalesce(func.sum(DatasetRecord.size_bytes), 0))
                    .join(
                        ProjectRecord,
                        ProjectRecord.id == DatasetRecord.project_id,
                    )
                    .join(
                        WorkspaceRecord,
                        WorkspaceRecord.id == ProjectRecord.workspace_id,
                    )
                    .where(
                        WorkspaceRecord.organization_id == organization_id,
                    )
                )
                return int(session.scalar(statement) or 0)

            if dimension is QuotaDimension.DATASET_COUNT:
                statement = (
                    select(func.count(DatasetRecord.id))
                    .join(
                        ProjectRecord,
                        ProjectRecord.id == DatasetRecord.project_id,
                    )
                    .join(
                        WorkspaceRecord,
                        WorkspaceRecord.id == ProjectRecord.workspace_id,
                    )
                    .where(
                        WorkspaceRecord.organization_id == organization_id,
                    )
                )
                return int(session.scalar(statement) or 0)

            if dimension is QuotaDimension.WORKFLOW_EXECUTION_COUNT:
                statement = (
                    select(func.count(WorkflowExecutionRecord.id))
                    .join(
                        WorkflowRecord,
                        WorkflowRecord.id == WorkflowExecutionRecord.workflow_id,
                    )
                    .join(
                        ProjectRecord,
                        ProjectRecord.id == WorkflowRecord.project_id,
                    )
                    .join(
                        WorkspaceRecord,
                        WorkspaceRecord.id == ProjectRecord.workspace_id,
                    )
                    .where(
                        WorkspaceRecord.organization_id == organization_id,
                    )
                )
                return int(session.scalar(statement) or 0)

            raise ValueError(f"Unsupported quota dimension: {dimension}")

