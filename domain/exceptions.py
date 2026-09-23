"""Application-level exceptions."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected application-level failures."""


class QuotaExceededError(ApplicationError):
    """Raised when an organization quota would be exceeded."""

    def __init__(
        self,
        *,
        dimension: str,
        current_usage: int,
        requested_usage: int,
        limit: int,
    ) -> None:
        self.dimension = dimension
        self.current_usage = current_usage
        self.requested_usage = requested_usage
        self.limit = limit

        super().__init__(
            f"Organization quota exceeded for {dimension}: "
            f"current usage {current_usage}, "
            f"requested increment {requested_usage}, "
            f"limit {limit}"
        )


class ComplianceViolationError(ApplicationError):
    """Raised when a governed operation violates compliance policy."""

    def __init__(
        self,
        *,
        organization_id: str,
        resource: str,
        action: str,
        reason: str,
    ) -> None:
        self.organization_id = organization_id
        self.resource = resource
        self.action = action
        self.reason = reason

        super().__init__(
            f"Compliance policy denied {resource}:{action}: {reason}"
        )


class ValidationRequestError(ApplicationError):
    """Raised when a validation request cannot be processed."""


class CapabilityError(Exception):
    """Base exception for capability-related errors."""


class CapabilityAlreadyRegisteredError(CapabilityError):
    """Raised when a capability ID is already registered."""


class CapabilityNotFoundError(CapabilityError):
    """Raised when a requested capability does not exist."""


class CapabilityDependencyError(Exception):
    """Base exception for capability dependency resolution errors."""


class CapabilityDependencyMissingError(CapabilityDependencyError):
    """Raised when a required capability does not exist."""


class CapabilityDependencyCycleError(CapabilityDependencyError):
    """Raised when capability dependencies contain a cycle."""


class CapabilityDependencyVersionError(
    CapabilityDependencyError
):
    """Raised when dependency version constraint is not satisfied."""


class CapabilityDependencyContractError(
    CapabilityDependencyError
):
    """Raised when capability input/output contracts are incompatible."""
