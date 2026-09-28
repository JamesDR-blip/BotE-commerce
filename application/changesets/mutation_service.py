"""Application service for atomic production ChangeSet application."""

from __future__ import annotations

import hashlib

from application.audit.audit_service import AuditService
from domain.changeset import ChangeSet
from services.compliance import ComplianceService


class ChangeSetMutationService:
    """Apply prepared ChangeSets through one database transaction."""

    def __init__(
        self,
        *,
        sessions,
        changesets,
        dataset_storage,
        audit_service: AuditService | None = None,
        compliance_service: ComplianceService | None = None,
    ) -> None:
        self._sessions = sessions
        self._changesets = changesets
        self._dataset_storage = dataset_storage
        self._audit_service = audit_service
        self._compliance_service = compliance_service

    def apply(
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

                if record.status != "PREPARED":
                    raise ValueError(
                        "Only PREPARED ChangeSets can be applied: "
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
                        f"Actor is not authorized to apply ChangeSet: "
                        f"{changeset_id}"
                    )
                actual_before_hash = self._hash_storage_artifact(
                    record.before_storage_key
                )
                if actual_before_hash != record.before_content_hash:
                    raise ValueError(
                        "ChangeSet before artifact hash mismatch: "
                        f"{changeset_id}"
                    )

                if self._compliance_service is not None:
                    organization_id = (
                        self._changesets.get_organization_id_in_transaction(
                            session,
                            changeset_id,
                        )
                    )

                    if organization_id is not None:
                        self._compliance_service.check(
                            organization_id=organization_id,
                            resource="changeset",
                            action="apply",
                            context={
                                "workflow_id": record.workflow_id,
                            },
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

    def _hash_storage_artifact(self, storage_key: str) -> str:
        hasher = hashlib.sha256()
        with self._dataset_storage.open(storage_key=storage_key) as source:
            while chunk := source.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()


__all__ = ["ChangeSetMutationService"]
