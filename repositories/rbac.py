"""Persistence repository for enterprise RBAC."""
from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    MembershipRecord,
    PermissionRecord,
    RolePermissionRecord,
    RoleRecord,
)


class RBACRepository:
    """Read/write boundary for organization roles and permissions."""

    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    def create_role(
        self,
        *,
        role_id: str,
        name: str,
        description: str | None = None,
    ) -> RoleRecord:
        with self._sessions() as session:
            record = RoleRecord(
                id=role_id,
                name=name,
                description=description,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def create_permission(
        self,
        *,
        permission_id: str,
        resource: str,
        action: str,
    ) -> PermissionRecord:
        with self._sessions() as session:
            record = PermissionRecord(
                id=permission_id,
                resource=resource,
                action=action,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def assign_permission_to_role(
        self,
        *,
        role_id: str,
        permission_id: str,
    ) -> RolePermissionRecord:
        with self._sessions() as session:
            record = RolePermissionRecord(
                role_id=role_id,
                permission_id=permission_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def create_membership(
        self,
        *,
        membership_id: str,
        user_id: str,
        organization_id: str,
        role_id: str,
    ) -> MembershipRecord:
        with self._sessions() as session:
            record = MembershipRecord(
                id=membership_id,
                user_id=user_id,
                organization_id=organization_id,
                role_id=role_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def list_organization_ids_for_user(
        self,
        *,
        user_id: str,
    ) -> tuple[str, ...]:
        with self._sessions() as session:
            statement = (
                select(MembershipRecord.organization_id)
                .where(
                    MembershipRecord.user_id == user_id,
                )
                .distinct()
                .order_by(MembershipRecord.organization_id)
            )

            return tuple(session.scalars(statement).all())

    def list_permission_keys(
        self,
        *,
        user_id: str,
        organization_id: str | None = None,
    ) -> frozenset[str]:
        with self._sessions() as session:
            statement = (
                select(
                    PermissionRecord.resource,
                    PermissionRecord.action,
                )
                .join(
                    RolePermissionRecord,
                    RolePermissionRecord.permission_id == PermissionRecord.id,
                )
                .join(
                    RoleRecord,
                    RoleRecord.id == RolePermissionRecord.role_id,
                )
                .join(
                    MembershipRecord,
                    MembershipRecord.role_id == RoleRecord.id,
                )
                .where(MembershipRecord.user_id == user_id)
            )

            if organization_id is not None:
                statement = statement.where(
                    MembershipRecord.organization_id == organization_id
                )

            rows = session.execute(statement).all()

            return frozenset(
                f"{resource}:{action}"
                for resource, action in rows
            )

    def has_permission(
        self,
        *,
        user_id: str,
        permission_key: str,
        organization_id: str | None = None,
    ) -> bool:
        return permission_key in self.list_permission_keys(
            user_id=user_id,
            organization_id=organization_id,
        )
