"""Application query service for owner-scoped ChangeSets."""

from __future__ import annotations

from domain.identity import CurrentUser
from repositories.changesets import ChangeSetRepository


class ChangeSetQueryService:
    def __init__(
        self,
        *,
        changesets: ChangeSetRepository,
    ) -> None:
        self.changesets = changesets

    def list_changesets(
        self,
        *,
        current_user: CurrentUser,
    ):
        return self.changesets.list_for_owner(
            owner_id=current_user.user_id,
        )

    def get_changeset(
        self,
        *,
        current_user: CurrentUser,
        changeset_id: str,
    ):
        return self.changesets.get_for_owner(
            changeset_id=changeset_id,
            owner_id=current_user.user_id,
        )

    def get_items(
        self,
        *,
        current_user: CurrentUser,
        changeset_id: str,
    ):
        return self.changesets.list_items_for_owner(
            changeset_id=changeset_id,
            owner_id=current_user.user_id,
        )


__all__ = ["ChangeSetQueryService"]
