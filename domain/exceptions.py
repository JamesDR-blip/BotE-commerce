"""Application-level exceptions."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected application-level failures."""


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
    """Raised when a required capability is not registered."""


class CapabilityDependencyCycleError(CapabilityDependencyError):
    """Raised when capability dependencies contain a cycle."""