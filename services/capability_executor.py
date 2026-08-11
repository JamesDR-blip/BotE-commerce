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
            missing_inputs = [
                    key
                    for key in capability.spec.input_keys
                    if key not in context
                ]

            if missing_inputs:
                raise ValueError(
                    f"Missing required input for "
                    f"{step.capability_id}: {', '.join(missing_inputs)}"
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

            result = capability.execute(
                CapabilityContext(
                    execution_id=execution_id,
                    inputs=context,
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