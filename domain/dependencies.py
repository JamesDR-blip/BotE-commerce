"""Capability dependency resolution contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from domain.capabilities import CapabilitySpec


@dataclass(frozen=True)
class CapabilityDependency:
    """Dependency declaration between capabilities."""

    capability_id: str
    version_constraint: str = ""


class CapabilityDependencyResolver(Protocol):
    """Resolve capability dependencies into executable ordering."""

    def resolve(
        self,
        requested: Sequence[str],
        capabilities: Mapping[str, CapabilitySpec],
    ) -> tuple[CapabilitySpec, ...]:
        ...