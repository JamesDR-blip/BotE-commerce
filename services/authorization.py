from __future__ import annotations

from typing import TYPE_CHECKING

from domain.authorization import AuthorizationDecision, Permission, RoleName
from domain.identity import CurrentUser

if TYPE_CHECKING:
    from repositories.rbac import RBACRepository


ROLE_PERMISSIONS: dict[RoleName, frozenset[str]] = {
    RoleName.ADMIN: frozenset(
        {
            "workspace:read",
            "workspace:manage",
            "dataset:read",
            "dataset:write",
            "workflow:read",
            "workflow:write",
            "workflow:execute",
            "approval:read",
            "approval:decide",
        }
    ),
    RoleName.DATA_ENGINEER: frozenset(
        {
            "workspace:read",
            "dataset:read",
            "dataset:write",
            "workflow:read",
            "workflow:write",
            "workflow:execute",
        }
    ),
    RoleName.REVIEWER: frozenset(
        {
            "workspace:read",
            "dataset:read",
            "workflow:read",
            "approval:read",
            "approval:decide",
        }
    ),
    RoleName.VIEWER: frozenset(
        {
            "workspace:read",
            "dataset:read",
            "workflow:read",
            "approval:read",
        }
    ),
}


class AuthorizationService:
    """Application-facing authorization policy.

    When an RBAC repository is configured, persisted organization membership
    and permissions are authoritative. Without one, the legacy role matrix
    remains available for backward compatibility.

    Resource ownership and tenant scope remain separate concerns and are
    enforced by the relevant application/repository boundary.
    """

    def __init__(
        self,
        rbac_repository: RBACRepository | None = None,
    ) -> None:
        self.rbac_repository = rbac_repository

    def decide(
        self,
        *,
        user: CurrentUser,
        permission: Permission,
        organization_id: str | None = None,
    ) -> AuthorizationDecision:
        if self.rbac_repository is not None:
            allowed = self.rbac_repository.has_permission(
                user_id=user.user_id,
                permission_key=permission.key,
                organization_id=organization_id,
            )

            if allowed:
                scope = (
                    f" in organization '{organization_id}'"
                    if organization_id is not None
                    else ""
                )
                return AuthorizationDecision.allow(
                    f"Persisted RBAC grants '{permission.key}'"
                    f"{scope}"
                )

            return AuthorizationDecision.deny(
                f"User is not permitted to perform "
                f"'{permission.key}'"
                + (
                    f" in organization '{organization_id}'"
                    if organization_id is not None
                    else ""
                )
            )

        user_roles = {
            role
            for role in user.roles
            if role in {role_name.value for role_name in RoleName}
        }

        for role_value in user_roles:
            role = RoleName(role_value)
            if permission.key in ROLE_PERMISSIONS[role]:
                return AuthorizationDecision.allow(
                    f"Role '{role.value}' grants '{permission.key}'"
                )

        return AuthorizationDecision.deny(
            f"User is not permitted to perform '{permission.key}'"
        )

    def authorize(
        self,
        *,
        user: CurrentUser,
        action: str,
        resource: str,
        organization_id: str | None = None,
    ) -> None:
        permission = Permission(
            resource=resource,
            action=action,
        )
        decision = self.decide(
            user=user,
            permission=permission,
            organization_id=organization_id,
        )

        if not decision.allowed:
            raise PermissionError(decision.reason)
