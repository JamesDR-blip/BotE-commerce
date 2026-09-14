"""Application service for atomic ChangeSet rollback."""

from __future__ import annotations

from application.audit.audit_service import AuditService
from domain.changeset import ChangeSet


class ChangeSetRollbackService:
    """Rollback an applied ChangeSet through one database transaction."""

    def __init__(
        self,
        *,
        sessions,
        changesets,
        audit_service: AuditService | None = None,
    ) -> None:
        self._sessions = sessions
        self._changesets = changesets
        self._audit_service = audit_service

    def rollback(
        self,
        *,
        changeset_id: str,
        actor_id: str | None = None,
    ) -> ChangeSet:
        with self._sessions() as session:
            with session.begin():
                record = self._changesets.get_record_in_transaction(
                    session,
                    changeset_id,
                )

                if record is None:
                    raise ValueError(
                        f"ChangeSet not found: {changeset_id}"
                    )

                if record.status != "APPLIED":
                    raise ValueError(
                        "Only APPLIED ChangeSets can be rolled back: "
                        f"{changeset_id} ({record.status})"
                    )

                rolled_back = self._changesets.rollback_in_transaction(
                    session,
                    changeset_id=changeset_id,
                    expected_after_storage_key=(
                        record.after_storage_key
                    ),
                )

                if self._audit_service is not None and actor_id is not None:
                    workspace_id = (
                        self._changesets.get_workspace_id_in_transaction(
                            session,
                            changeset_id,
                        )
                    )

                    if workspace_id is None:
                        raise ValueError(
                            "Workspace not found for ChangeSet: "
                            f"{changeset_id}"
                        )

                    self._audit_service.record_in_transaction(
                        session,
                        workspace_id=workspace_id,
                        actor_id=actor_id,
                        action="CHANGESET_ROLLED_BACK",
                        resource_type="changeset",
                        resource_id=changeset_id,
                        execution_id=rolled_back.execution_id,
                        changeset_id=changeset_id,
                        metadata={
                            "dataset_id": rolled_back.dataset_id,
                            "status": "ROLLED_BACK",
                            "before_storage_key": (
                                rolled_back.before_storage_key
                            ),
                            "before_content_hash": (
                                rolled_back.before_content_hash
                            ),
                            "after_storage_key": (
                                rolled_back.after_storage_key
                            ),
                            "after_content_hash": (
                                rolled_back.after_content_hash
                            ),
                        },
                    )

            return self._changesets.to_domain(rolled_back)


__all__ = ["ChangeSetRollbackService"]
