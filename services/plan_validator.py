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

        for step in plan.steps:
            capability = registry.get(step.capability_id)
            spec = capability.spec

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

            available_outputs.update(spec.output_keys)


__all__ = [
    "PlanValidator",
]