"""Application-owned persistence contracts for ChangeSet use cases."""

from __future__ import annotations

from typing import Protocol

from domain.changeset import ChangeSet, ChangeSetItem


class ChangeSetQueryPersistencePort(Protocol):
    """Persistence operations required by ChangeSet query use cases."""

    def list_for_owner(
        self,
        *,
        owner_id: str,
    ) -> list[ChangeSet]: ...

    def get_for_owner(
        self,
        *,
        changeset_id: str,
        owner_id: str,
    ) -> ChangeSet | None: ...

    def list_items_for_owner(
        self,
        *,
        changeset_id: str,
        owner_id: str,
    ) -> list[ChangeSetItem] | None: ...
