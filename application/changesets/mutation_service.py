"""Application service for atomic production ChangeSet application."""

from __future__ import annotations

from domain.changeset import ChangeSet


class ChangeSetMutationService:
    """Apply prepared ChangeSets through one database transaction."""

    def __init__(
        self,
        *,
        sessions,
        changesets,
    ) -> None:
        self._sessions = sessions
        self._changesets = changesets

    def apply(
        self,
        *,
        changeset_id: str,
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

            return self._changesets.to_domain(applied)


__all__ = ["ChangeSetMutationService"]
