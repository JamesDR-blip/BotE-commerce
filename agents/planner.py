from __future__ import annotations

from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec
from domain.capability_registry import CapabilityRegistry
from domain.capability_selector import CapabilitySelector
from domain.plans import ExecutionPlan, PlanStep
from domain.type_contracts import TYPE_CONTRACTS

from .requirement import ValidationRequirement


class PlannerAgent:
    """Build deterministic execution plans from registered capabilities."""

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        resolver: DependencyResolver | None = None,
        catalog: dict[str, CapabilitySpec] | None = None,
        selector: CapabilitySelector | None = None,
    ) -> None:
        if registry is not None and catalog is not None:
            raise ValueError(
                "PlannerAgent accepts either registry or catalog, not both"
            )

        self._registry = registry
        self._catalog_snapshot = catalog
        self._resolver = resolver or DependencyResolver()

        if selector is not None:
            self._selector = selector
        elif registry is not None:
            self._selector = CapabilitySelector(
                lambda: registry.catalog().keys()
            )
        else:
            self._selector = CapabilitySelector(
                lambda: (catalog or {}).keys()
            )
    @property
    def _catalog(self) -> dict[str, CapabilitySpec]:
        if self._registry is not None:
            return self._registry.catalog()

        return self._catalog_snapshot or {}

    def _validate_dependency_mapping(
        self,
        spec: CapabilitySpec,
        input_mapping: dict[str, str],
        available_outputs: set[str],
        allow_external: bool = False,
    ) -> None:

        unknown_sources = [
            source
            for source in input_mapping.values()
            if (
                source not in available_outputs
                and source not in spec.input_keys
                and not allow_external
            )
        ]

        if unknown_sources:
            raise ValueError(
                f"Unknown input mapping source for "
                f"{spec.id}: "
                + ", ".join(unknown_sources)
            )

    def _validate_input_mapping(
        self,
        spec: CapabilitySpec,
        input_mapping: dict[str, str],
        previous_outputs: set[str],
    ) -> None:
        unknown_input_keys = [
            key
            for key in input_mapping
            if key not in spec.input_keys
        ]

        if unknown_input_keys:
            raise ValueError(
                f"Unknown input mapping key for "
                f"{spec.id}: "
                f"{', '.join(unknown_input_keys)}"
            )

        unknown_sources = [
            source
            for source in input_mapping.values()
            if source not in previous_outputs
        ]

        if unknown_sources:
            raise ValueError(
                f"Unknown input mapping source for "
                f"{spec.id}: "
                f"{', '.join(unknown_sources)}"
            )

    def _validate_type_contract(
        self,
        spec: CapabilitySpec,
    ) -> None:
        for key, declared_type in spec.input_types.items():
            if key not in TYPE_CONTRACTS:
                raise TypeError(
                    f"Unknown input type contract: {key}"
                )

            expected_type = TYPE_CONTRACTS[key]

            if declared_type is not expected_type:
                raise TypeError(
                    f"Invalid input type for "
                    f"{spec.id}: {key}"
                )

        for key, declared_type in spec.output_types.items():
            if key not in TYPE_CONTRACTS:
                raise TypeError(
                    f"Unknown output type contract: {key}"
                )

            expected_type = TYPE_CONTRACTS[key]

            if (
                expected_type is not object
                and declared_type is not expected_type
            ):
                raise TypeError(
                    f"Invalid output type for "
                    f"{spec.id}: {key}"
                )

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

        requested_capabilities = requirement.requested_capabilities

        if self._selector is not None:
            requested_capabilities = self._selector.select(
                requirement
            )

        specs = self._resolver.resolve(
            requested=requested_capabilities,
            capabilities=catalog,
        )

        for spec in specs:
            self._validate_type_contract(spec)

        planned_capability_ids = {
            spec.id
            for spec in specs
        }

        requirement_mappings = requirement.input_mappings or {}
        requirement_parameters = requirement.parameters or {}

        for capability_id in requirement_mappings:
            if capability_id not in planned_capability_ids:
                raise ValueError(
                    f"Input mapping target capability "
                    f"that is not planned: "
                    f"{capability_id}"
                )

        for capability_id, parameters in requirement_parameters.items():
            if capability_id not in planned_capability_ids:
                raise ValueError(
                    f"Parameters target capability "
                    f"that is not planned: "
                    f"{capability_id}"
                )

            spec = catalog[capability_id]

            unknown_parameters = [
                key
                for key in parameters
                if key not in spec.parameter_keys
            ]

            if unknown_parameters:
                raise ValueError(
                    f"Unknown parameter for "
                    f"{capability_id}: "
                    f"{', '.join(unknown_parameters)}"
                )

        steps_list: list[PlanStep] = []
        available_outputs: set[str] = set()

        for spec in specs:
            has_requirement_mapping = spec.id in requirement_mappings

            if has_requirement_mapping:
                input_mapping = dict(
                    requirement_mappings[spec.id]
                )
            else:
                input_mapping = dict(spec.input_mappings)

            self._validate_dependency_mapping(
                spec,
                input_mapping,
                available_outputs,
                allow_external=has_requirement_mapping,
            )

            unknown_input_keys = [
                key
                for key in input_mapping
                if key not in spec.input_keys
            ]

            if unknown_input_keys:
                raise ValueError(
                    f"Unknown input mapping key for "
                    f"{spec.id}: "
                    f"{', '.join(unknown_input_keys)}"
                )

            if not has_requirement_mapping:
                unknown_sources = [
                    source
                    for source in input_mapping.values()
                    if (
                        source not in available_outputs
                        and source not in spec.input_keys
                    )
                ]

                if unknown_sources:
                    raise ValueError(
                        f"Unknown input mapping source for "
                        f"{spec.id}: "
                        f"{', '.join(unknown_sources)}"
                    )
                
            step = PlanStep(
                capability_id=spec.id,
                capability_version=spec.version,
                parameters=dict(
                    requirement_parameters.get(spec.id, {})
                ),
                input_mapping=input_mapping,
            )

            steps_list.append(step)
            available_outputs.update(spec.output_keys)

        steps = tuple(steps_list)

        return ExecutionPlan(
            steps=steps,
            metadata={"source": "planner"},
        )