"""Domain contracts for tenant-scoped resources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganizationResource:
    """Associates a resource with an organization boundary."""

    resource_id: str
    organization_id: str

    def __post_init__(self) -> None:
        if not self.resource_id.strip():
            raise ValueError("Resource id cannot be empty")
        if not self.organization_id.strip():
            raise ValueError("Organization id cannot be empty")
