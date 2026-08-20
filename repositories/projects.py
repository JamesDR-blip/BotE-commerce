"""Repository for project persistence."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ProjectRecord


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


    def list_by_workspace(
        self,
        workspace_id: str,
    ) -> list[ProjectRecord]:

        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ProjectRecord)
                    .where(
                        ProjectRecord.workspace_id
                        == workspace_id
                    )
                )
            )