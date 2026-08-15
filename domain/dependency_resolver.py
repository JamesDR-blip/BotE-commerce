"""Resolve capability dependencies into deterministic execution order."""

from __future__ import annotations

from typing import Mapping, Sequence

from domain.capabilities import CapabilitySpec
from domain.dependencies import CapabilityDependencyResolver
from domain.dependencies import CapabilityDependency
from domain.versioning import satisfies
from domain.exceptions import (
    CapabilityDependencyCycleError,
    CapabilityDependencyMissingError,
    CapabilityDependencyVersionError,
    CapabilityDependencyContractError,
)

from packaging.version import Version


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

            for dependency in spec.required_capabilities:

                if isinstance(dependency, str):
                    dependency_id = dependency
                    version_constraint = None

                else:
                    dependency_id = dependency.capability_id
                    version_constraint = dependency.version_constraint

                dependency_spec = capabilities.get(
                    dependency_id
                )

                if dependency_spec is None:
                    raise CapabilityDependencyMissingError(
                        f"Capability dependency not found: {dependency_id}"
                    )

                if version_constraint:
                    self._validate_version(
                        dependency_spec,
                        version_constraint,
                    )

                self._validate_dependency_contract(
                    dependency_spec,
                    spec,
                )

                visit(dependency_id)

            visiting.remove(capability_id)
            visited.add(capability_id)
            resolved.append(spec)

        for capability_id in requested:
            visit(capability_id)

        return tuple(resolved)

    def _validate_version(
        self,
        spec: CapabilitySpec,
        constraint: str,
    ) -> None:

        current = Version(spec.version)

        if constraint.startswith(">="):
            required = Version(
                constraint.replace(">=", "").strip()
            )

            if current < required:
                raise CapabilityDependencyVersionError(
                    f"{spec.id} version {spec.version} "
                    f"does not satisfy {constraint}"
                )

    def _validate_dependency_contract(
        self,
        dependency: CapabilitySpec,
        consumer: CapabilitySpec,
    ) -> None:

        # Explicit mapping sẽ được Planner xử lý
        if consumer.input_mappings:
            return

        # Dependency contract validation
        missing_inputs = [
            key
            for key in consumer.input_keys
            if (
                key.endswith("_frame")
                or key.endswith("_result")
                or key.endswith("_data")
            )
            and key not in dependency.output_keys
        ]

        if missing_inputs:
            raise CapabilityDependencyContractError(
                f"{dependency.id} does not provide "
                f"required inputs for {consumer.id}: "
                + ", ".join(missing_inputs)
            )
        
__all__ = ["DependencyResolver"]