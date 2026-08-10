"""Resolve capability dependencies into deterministic execution order."""

from __future__ import annotations

from typing import Mapping, Sequence

from domain.capabilities import CapabilitySpec
from domain.dependencies import CapabilityDependencyResolver
from domain.exceptions import (
    CapabilityDependencyCycleError,
    CapabilityDependencyMissingError,
)


class DependencyResolver:
    """Resolve capability dependencies using deterministic depth-first traversal."""

    def resolve(
        self,
        requested: Sequence[str],
        capabilities: Mapping[str, CapabilitySpec],
    ) -> tuple[CapabilitySpec, ...]:
        resolved: list[CapabilitySpec] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(capability_id: str) -> None:
            if capability_id in visited:
                return

            if capability_id in visiting:
                raise CapabilityDependencyCycleError(
                    f"Capability dependency cycle detected: {capability_id}"
                )

            if capability_id not in capabilities:
                raise CapabilityDependencyMissingError(
                    f"Capability dependency not found: {capability_id}"
                )

            visiting.add(capability_id)

            spec = capabilities[capability_id]

            for dependency_id in spec.required_capabilities:
                visit(dependency_id)

            visiting.remove(capability_id)
            visited.add(capability_id)
            resolved.append(spec)

        for capability_id in requested:
            visit(capability_id)

        return tuple(resolved)


__all__ = ["DependencyResolver"]