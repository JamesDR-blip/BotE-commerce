"""Capability dependency value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDependency:
    """A capability dependency requirement."""

    capability_id: str
    version_constraint: str | None = None


__all__ = [
    "CapabilityDependency",
]