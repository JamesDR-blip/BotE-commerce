"""Domain contracts for enterprise authorization and tenant membership."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "admin"
    DATA_ENGINEER = "data_engineer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


@dataclass(frozen=True)
class Permission:
    """A single action that can be granted to a role."""

    resource: str
    action: str

    def __post_init__(self) -> None:
        if not self.resource.strip():
            raise ValueError("Permission resource cannot be empty")
        if not self.action.strip():
            raise ValueError("Permission action cannot be empty")

    @property
    def key(self) -> str:
        return f"{self.resource}:{self.action}"


@dataclass(frozen=True)
class Organization:
    """Tenant boundary for governed application resources."""

    id: str
    name: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Organization id cannot be empty")
        if not self.name.strip():
            raise ValueError("Organization name cannot be empty")


@dataclass(frozen=True)
class Membership:
    """A user's membership and role within an organization."""

    user_id: str
    organization_id: str
    role: RoleName

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("Membership user_id cannot be empty")
        if not self.organization_id.strip():
            raise ValueError("Membership organization_id cannot be empty")


@dataclass(frozen=True)
class AuthorizationDecision:
    """Result of an authorization evaluation."""

    allowed: bool
    reason: str

    @classmethod
    def allow(
        cls,
        reason: str = "Permission granted",
    ) -> "AuthorizationDecision":
        return cls(allowed=True, reason=reason)

    @classmethod
    def deny(cls, reason: str) -> "AuthorizationDecision":
        if not reason.strip():
            raise ValueError(
                "Authorization denial reason cannot be empty"
            )
        return cls(allowed=False, reason=reason)
