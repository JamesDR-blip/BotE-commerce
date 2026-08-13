"""Execute capability-driven execution plans."""

from __future__ import annotations

from typing import Any, Mapping

from domain.capability_registry import CapabilityRegistry
from domain.capabilities import CapabilityContext
from domain.plans import ExecutionPlan


class CapabilityExecutor:
    """Execute capabilities in the order defined by an execution plan."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        plan: ExecutionPlan,
        inputs: Mapping[str, Any],
        execution_id: str,
    ) -> dict[str, Any]:
        context: dict[str, Any] = dict(inputs)

        for step in plan.steps:
            capability = self._registry.get(step.capability_id)

            if capability.spec.version != step.capability_version:
                raise ValueError(
                    f"Capability version mismatch for "
                    f"{step.capability_id}: "
                    f"plan requires {step.capability_version}, "
                    f"registered capability is {capability.spec.version}"
                )

            unknown_mappings = [
                key
                for key in step.input_mapping
                if key not in capability.spec.input_keys
            ]

            if unknown_mappings:
                raise ValueError(
                    f"Unknown input mapping for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_mappings)}"
                )
            
            unknown_parameters = [
                key
                for key in step.parameters
                if key not in capability.spec.parameter_keys
            ]

            if unknown_parameters:
                raise ValueError(
                    f"Unknown parameter for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_parameters)}"
                )

            mapped_inputs = {}

            for input_key in capability.spec.input_keys:
                source_key = step.input_mapping.get(input_key, input_key)

                if source_key not in context:
                    raise ValueError(
                        f"Missing required input for "
                        f"{step.capability_id}: "
                        f"{input_key} "
                        f"(source: {source_key})"
                    )

                mapped_inputs[input_key] = context[source_key]

            result = capability.execute(
                CapabilityContext(
                    execution_id=execution_id,
                    inputs=mapped_inputs,
                    config=step.parameters,
                )
            )

            undeclared_outputs = [
                key
                for key in result.outputs
                if key not in capability.spec.output_keys
            ]

            if undeclared_outputs:
                raise ValueError(
                    f"Undeclared output for "
                    f"{step.capability_id}: "
                    f"{', '.join(undeclared_outputs)}"
                )

            context.update(result.outputs)

        return context


__all__ = ["CapabilityExecutor"]