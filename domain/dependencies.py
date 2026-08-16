"""Capability dependency resolution contracts."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence

from domain.capabilities import CapabilitySpec


class CapabilityDependencyResolver(Protocol):
    """Resolve capability dependencies into executable ordering."""

    def resolve(
        self,
        requested: Sequence[str],
        capabilities: Mapping[str, CapabilitySpec],
    ) -> tuple[CapabilitySpec, ...]:
        ...


__all__ = [
    "CapabilityDependencyResolver",
]