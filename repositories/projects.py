"""Repository for project persistence."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ProjectRecord, WorkspaceRecord


class ProjectRepository:

    def __init__(
        self,
        sessions: Callable[[], Session],
    ) -> None:
        self._sessions = sessions

    def create(
        self,
        *,
        project_id: str,
        workspace_id: str,
        name: str,
        description: str | None = None,
    ) -> ProjectRecord:

        with self._sessions() as session:
            record = ProjectRecord(
                id=project_id,
                workspace_id=workspace_id,
                name=name,
                description=description,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def get(
        self,
        project_id: str,
    ) -> ProjectRecord | None:

        with self._sessions() as session:
            return session.get(
                ProjectRecord,
                project_id,
            )

    def get_for_owner(
        self,
        *,
        project_id: str,
        owner_id: str,
    ) -> ProjectRecord | None:

        with self._sessions() as session:
            return session.scalar(
                select(ProjectRecord)
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ProjectRecord.id == project_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

    def get_for_organization(
        self,
        *,
        project_id: str,
        organization_id: str,
    ) -> ProjectRecord | None:

        with self._sessions() as session:
            return session.scalar(
                select(ProjectRecord)
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ProjectRecord.id == project_id,
                    WorkspaceRecord.organization_id == organization_id,
                )
            )

    def get_for_owner_in_organization(
        self,
        *,
        project_id: str,
        owner_id: str,
        organization_id: str,
    ) -> ProjectRecord | None:

        with self._sessions() as session:
            return session.scalar(
                select(ProjectRecord)
                .join(
                    WorkspaceRecord,
                    ProjectRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ProjectRecord.id == project_id,
                    WorkspaceRecord.owner_id == owner_id,
                    WorkspaceRecord.organization_id == organization_id,
                )
            )

    def list_by_workspace(
        self,
        workspace_id: str,
    ) -> list[ProjectRecord]:

        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ProjectRecord).where(
                        ProjectRecord.workspace_id == workspace_id
                    )
                )
            )
