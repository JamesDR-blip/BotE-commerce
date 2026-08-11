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

            result = capability.execute(
                CapabilityContext(
                    execution_id=execution_id,
                    inputs=context,
                    config=step.parameters,
                )
            )

            context.update(result.outputs)

        return context


__all__ = ["CapabilityExecutor"]