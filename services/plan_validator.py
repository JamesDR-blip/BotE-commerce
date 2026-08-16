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

        for step in plan.steps:
            capability = registry.get(step.capability_id)
            spec = capability.spec

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

            produced_outputs.update(spec.output_keys)
            available_outputs.update(spec.output_keys)


__all__ = [
    "PlanValidator",
]