"""Application-level exceptions."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for expected application-level failures."""


class ValidationRequestError(ApplicationError):
    """Raised when a validation request cannot be processed."""