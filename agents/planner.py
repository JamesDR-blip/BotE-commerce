from __future__ import annotations

from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep

from .requirement import ValidationRequirement


class PlannerAgent:
    """Build deterministic execution plans from registered capabilities."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        resolver: DependencyResolver | None = None,
        catalog: dict[str, CapabilitySpec] | None = None,
    ) -> None:
        if registry is not None and catalog is not None:
            raise ValueError(
                "PlannerAgent accepts either registry or catalog, not both"
            )

        self._registry = registry
        self._catalog_snapshot = catalog
        self._resolver = resolver or DependencyResolver()

    @property
    def _catalog(self) -> dict[str, CapabilitySpec]:
        if self._registry is not None:
            return self._registry.catalog()

        return self._catalog_snapshot or {}

    def plan(self, requirement: ValidationRequirement) -> ExecutionPlan:
        """Build an execution plan from a validated requirement."""

        if self._registry is None and self._catalog_snapshot is None:
            raise ValueError(
                "Planner requires a capability registry or catalog"
            )

        catalog = (
            self._registry.catalog()
            if self._registry is not None
            else self._catalog_snapshot
        )

        specs = self._resolver.resolve(
            requested=requirement.requested_capabilities,
            capabilities=catalog,
        )

        requirement_mappings = requirement.input_mappings or {}
        requirement_parameters = requirement.parameters or {}

        steps = tuple(
            PlanStep(
                capability_id=spec.id,
                capability_version=spec.version,
                parameters=dict(
                    requirement_parameters.get(spec.id, {})
                ),
                input_mapping=dict(
                    requirement_mappings.get(
                        spec.id,
                        dict(spec.input_mappings),
                    )
                ),
            )
            for spec in specs
        )

        return ExecutionPlan(
            steps=steps,
            metadata={"source": "planner"},
        )