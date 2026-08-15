"""Validate execution plans before execution."""

from __future__ import annotations

from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan


class PlanValidator:
    """Validate execution plan against capability registry."""

    def validate(
        self,
        plan: ExecutionPlan,
        registry: CapabilityRegistry,
    ) -> None:
        for step in plan.steps:
            capability = registry.get(step.capability_id)

            if capability.spec.version != step.capability_version:
                raise ValueError(
                    f"Capability version mismatch for "
                    f"{step.capability_id}: "
                    f"plan requires {step.capability_version}, "
                    f"registered capability is "
                    f"{capability.spec.version}"
                )