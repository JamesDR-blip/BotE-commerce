"""Application service for atomic ChangeSet rollback."""

from __future__ import annotations

import hashlib

from application.audit.audit_service import AuditService
from domain.changeset import ChangeSet


class ChangeSetRollbackService:
    """Rollback an applied ChangeSet through one database transaction."""

    def __init__(
        self,
        *,
        sessions,
        changesets,
        dataset_storage,
        audit_service: AuditService | None = None,
    ) -> None:
        self._sessions = sessions
        self._changesets = changesets
        self._dataset_storage = dataset_storage
        self._audit_service = audit_service

    def rollback(
        self,
        *,
        changeset_id: str,
        actor_id: str,
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

                owner_id = self._changesets.get_owner_id_in_transaction(
                    session,
                    changeset_id,
                )

                if owner_id is None:
                    raise ValueError(
                        "Owner not found for ChangeSet: "
                        f"{changeset_id}"
                    )

                if actor_id != owner_id:
                    raise PermissionError(
                        f"Actor is not authorized to rollback ChangeSet: "
                        f"{changeset_id}"
                    )
                actual_after_hash = self._hash_storage_artifact(
                    record.after_storage_key
                )
                if actual_after_hash != record.after_content_hash:
                    raise ValueError(
                        "ChangeSet after artifact hash mismatch: "
                        f"{changeset_id}"
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

    def _hash_storage_artifact(self, storage_key: str) -> str:
        hasher = hashlib.sha256()
        with self._dataset_storage.open(storage_key=storage_key) as source:
            while chunk := source.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()


__all__ = ["ChangeSetRollbackService"]
