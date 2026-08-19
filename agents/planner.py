from __future__ import annotations

from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec
from domain.capability_registry import CapabilityRegistry
from domain.capability_selector import CapabilitySelector
from domain.plans import ExecutionPlan, PlanStep
from domain.intent_resolver import IntentResolver
from domain.exceptions import CapabilityDependencyContractError
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
        intent_resolver: IntentResolver | None = None,
    ) -> None:
        if registry is not None and catalog is not None:
            raise ValueError(
                "PlannerAgent accepts either registry or catalog, not both"
            )

        self._registry = registry
        self._catalog_snapshot = catalog
        self._resolver = resolver or DependencyResolver()
        self._intent_resolver = intent_resolver

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

    def _validate_type_contract(
        self,
        spec: CapabilitySpec,
    ) -> None:
        for key, declared_type in spec.input_types.items():
            if key not in spec.input_keys:
                raise TypeError(
                    f"Input type declared for unknown input "
                    f"{spec.id}: {key}"
                )

            if not isinstance(declared_type, type):
                raise TypeError(
                    f"Invalid input type declaration for "
                    f"{spec.id}: {key}"
                )

        for key, declared_type in spec.output_types.items():
            if key not in spec.output_keys:
                raise TypeError(
                    f"Output type declared for unknown output "
                    f"{spec.id}: {key}"
                )

            if not isinstance(declared_type, type):
                raise TypeError(
                    f"Invalid output type declaration for "
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

        requested_capabilities = (
            requirement.requested_capabilities
        )

        if (
            not requested_capabilities
            and requirement.requested_intents
            and self._intent_resolver
        ):
            requested_capabilities = (
                self._intent_resolver.resolve(
                    requirement.requested_intents
                )
            )

        if self._selector is not None:
            requested_capabilities = self._selector.select(
                ValidationRequirement(
                    requested_capabilities=requested_capabilities,
                )
            )

        try:
            specs = self._resolver.resolve(
                requested=requested_capabilities,
                capabilities=catalog,
            )
        except CapabilityDependencyContractError as exc:
            raise ValueError(
                f"Unknown input mapping source: {exc}"
            ) from exc
        
        requirement_mappings = requirement.input_mappings or {}
        requirement_parameters = requirement.parameters or {}

        planned_capability_ids = {
            spec.id
            for spec in specs
        }

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
        available_output_types: dict[str, type] = {}
        output_owners: dict[str, str] = {}

        for spec in specs:
            has_requirement_mapping = spec.id in requirement_mappings

            if has_requirement_mapping:
                input_mapping = dict(
                    requirement_mappings[spec.id]
                )
            else:
                input_mapping = dict(spec.input_mappings)

            self._validate_type_contract(spec)

            self._validate_input_contract(
                spec,
                input_mapping=input_mapping,
                available_output_types=available_output_types,
            )

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

            for output in spec.output_keys:
                if output not in available_outputs:
                    continue

                # A capability may consume an existing value
                # and intentionally replace it under the same key.
                if output in spec.input_keys:
                    continue

                previous_owner = output_owners.get(output)

                if previous_owner is not None:
                    raise ValueError(
                        f"Output collision for "
                        f"{spec.id}: "
                        f"{output}"
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

            for output in spec.output_keys:
                available_outputs.add(output)
                output_owners[output] = spec.id

            available_output_types.update(
                spec.output_types
            )

        steps = tuple(steps_list)

        return ExecutionPlan(
            steps=steps,
            metadata={"source": "planner"},
        )

    def _validate_input_contract(
        self,
        spec: CapabilitySpec,
        input_mapping: dict[str, str] | None = None,
        available_output_types: dict[str, type] | None = None,
    ) -> None:
        input_mapping = input_mapping or {}
        available_output_types = (
            available_output_types
            if available_output_types is not None
            else {}
        )

        for key, expected_type in spec.input_types.items():
            if key not in spec.input_keys:
                raise TypeError(
                    f"Input type declared for unknown input "
                    f"{spec.id}: {key}"
                )

            if not isinstance(expected_type, type):
                raise TypeError(
                    f"Invalid input type declaration for "
                    f"{spec.id}: {key}"
                )

            source_key = input_mapping.get(key)

            if source_key is not None:
                if source_key in available_output_types:
                    provided_type = available_output_types[source_key]

                    if not issubclass(
                        provided_type,
                        expected_type,
                    ):
                        raise TypeError(
                            f"Incompatible input type for "
                            f"{spec.id}: "
                            f"{key} expects "
                            f"{expected_type.__name__}, "
                            f"but mapped source "
                            f"{source_key} provides "
                            f"{provided_type.__name__}"
                        )

                    continue

                # Requirement mappings may refer to
                # external inputs. Those are validated
                # through TYPE_CONTRACTS when known.
                if source_key in TYPE_CONTRACTS:
                    provided_type = TYPE_CONTRACTS[source_key]

                    if not issubclass(
                        provided_type,
                        expected_type,
                    ):
                        raise TypeError(
                            f"Incompatible input type for "
                            f"{spec.id}: "
                            f"{key} expects "
                            f"{expected_type.__name__}, "
                            f"but system provides "
                            f"{provided_type.__name__}"
                        )

                    continue

            elif key in available_output_types:
                # An unmapped input resolves by key name.
                # If a previous capability already produced that key,
                # its output type is the actual contract.
                provided_type = available_output_types[key]

                if not issubclass(
                    provided_type,
                    expected_type,
                ):
                    raise TypeError(
                        f"Incompatible input type for "
                        f"{spec.id}: "
                        f"{key} expects "
                        f"{expected_type.__name__}, "
                        f"but previous output "
                        f"{key} provides "
                        f"{provided_type.__name__}"
                    )

                continue

            elif key in TYPE_CONTRACTS:
                provided_type = TYPE_CONTRACTS[key]

                if not issubclass(
                    provided_type,
                    expected_type,
                ):
                    raise TypeError(
                        f"Incompatible input type for "
                        f"{spec.id}: "
                        f"{key} expects "
                        f"{expected_type.__name__}, "
                        f"but system provides "
                        f"{provided_type.__name__}"
                    )

        for key, declared_type in spec.output_types.items():
            if key not in spec.output_keys:
                raise TypeError(
                    f"Output type declared for unknown output "
                    f"{spec.id}: {key}"
                )

            if not isinstance(declared_type, type):
                raise TypeError(
                    f"Invalid output type declaration for "
                    f"{spec.id}: {key}"
                )