"""Validate execution plans before execution."""

from __future__ import annotations

from typing import Collection

from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan


class PlanValidator:
    """Validate execution plan against capability registry."""

    def validate(
        self,
        plan: ExecutionPlan,
        registry: CapabilityRegistry,
        external_inputs: Collection[str] = (),
    ) -> None:
        available_outputs = set(external_inputs)
        produced_outputs: set[str] = set()

        output_owners: dict[str, str] = {}
        output_types: dict[str, type] = {}

        available_output_types = {}

        for step in plan.steps:
            capability = registry.get(step.capability_id)

            spec = capability.spec

            for output in spec.output_keys:
                if output in produced_outputs:
                    previous_owner = output_owners[output]

                    previous_type = output_types.get(output)
                    current_type = spec.output_types.get(output)

                    if (
                        previous_owner != step.capability_id
                        and previous_type is not None
                        and current_type is not None
                        and previous_type != current_type
                    ):
                        raise ValueError(
                            f"Output collision for "
                            f"{step.capability_id}: "
                            f"{output}"
                        )

            output_collisions = [
                output
                for output in spec.output_keys
                if (
                    output in produced_outputs
                    and output not in spec.input_keys
                )
            ]

            if output_collisions:
                raise ValueError(
                    f"Output collision for "
                    f"{step.capability_id}: "
                    f"{', '.join(output_collisions)}"
                )

            if spec.version != step.capability_version:
                raise ValueError(
                    f"Capability version mismatch for "
                    f"{step.capability_id}: "
                    f"plan requires {step.capability_version}, "
                    f"registered capability is "
                    f"{spec.version}"
                )

            unknown_parameters = [
                key
                for key in step.parameters
                if key not in spec.parameter_keys
            ]

            if unknown_parameters:
                raise ValueError(
                    f"Unknown parameter for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_parameters)}"
                )

            unknown_mappings = [
                key
                for key in step.input_mapping
                if key not in spec.input_keys
            ]

            if unknown_mappings:
                raise ValueError(
                    f"Unknown input mapping for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_mappings)}"
                )

            mapped_input_keys = set(step.input_mapping)

            for input_key in spec.input_keys:
                if input_key in mapped_input_keys:
                    continue

                if input_key in available_outputs:
                    continue

                raise ValueError(
                    f"Missing required input for "
                    f"{step.capability_id}: "
                    f"{input_key}"
                )

            unknown_sources = [
                source
                for source in step.input_mapping.values()
                if source not in available_outputs
            ]

            if unknown_sources:
                raise ValueError(
                    f"Unknown input mapping source for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_sources)}"
                )
            
            for input_key, source_key in step.input_mapping.items():
                self._validate_mapping_types(
                    source_key,
                    input_key,
                    available_output_types,
                    spec.input_types,
                    step.capability_id,
                )

            produced_outputs.update(spec.output_keys)

            for output in spec.output_keys:
                previous_owner = output_owners.get(output)

                if (
                    previous_owner
                    and previous_owner != step.capability_id
                    and output not in spec.input_keys
                ):
                    raise ValueError(
                        f"Output collision for "
                        f"{step.capability_id}: {output}"
                    )

                output_owners[output] = step.capability_id
                
                if output in spec.output_types:
                    output_types[output] = spec.output_types[output]

            available_outputs.update(spec.output_keys)

            available_output_types.update(
                spec.output_types
            )

    def _validate_mapping_types(
        self,
        source_key: str,
        target_key: str,
        source_types,
        target_types,
        capability_id: str,
    ) -> None:
        if (
            source_key not in source_types
            or target_key not in target_types
        ):
            return

        source_type = source_types[source_key]
        target_type = target_types[target_key]

        if not issubclass(
            source_type,
            target_type,
        ):
            raise TypeError(
                f"Incompatible input type for "
                f"{capability_id}: "
                f"{target_key} expects "
                f"{target_type.__name__}, "
                f"but mapped source "
                f"{source_key} provides "
                f"{source_type.__name__}"
            )


__all__ = [
    "PlanValidator",
]