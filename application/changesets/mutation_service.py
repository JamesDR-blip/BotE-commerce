"""Application service for atomic production ChangeSet application."""

from __future__ import annotations

from application.audit.audit_service import AuditService
from domain.changeset import ChangeSet


class ChangeSetMutationService:
    """Apply prepared ChangeSets through one database transaction."""

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

    def apply(
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

                if record.status != "PREPARED":
                    raise ValueError(
                        "Only PREPARED ChangeSets can be applied: "
                        f"{changeset_id} ({record.status})"
                    )

                applied = self._changesets.apply_in_transaction(
                    session,
                    changeset_id=changeset_id,
                    expected_before_storage_key=(
                        record.before_storage_key
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
                        action="CHANGESET_APPLIED",
                        resource_type="changeset",
                        resource_id=changeset_id,
                        execution_id=applied.execution_id,
                        changeset_id=changeset_id,
                        metadata={
                            "dataset_id": applied.dataset_id,
                            "status": "APPLIED",
                            "before_storage_key": (
                                applied.before_storage_key
                            ),
                            "before_content_hash": (
                                applied.before_content_hash
                            ),
                            "after_storage_key": (
                                applied.after_storage_key
                            ),
                            "after_content_hash": (
                                applied.after_content_hash
                            ),
                        },
                    )

            return self._changesets.to_domain(applied)


__all__ = ["ChangeSetMutationService"]
