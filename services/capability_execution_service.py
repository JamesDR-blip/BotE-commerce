"""Application service for planning and executing capabilities."""

from __future__ import annotations

from typing import Any, Mapping

from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from services.capability_executor import CapabilityExecutor
from services.plan_validator import PlanValidator


class CapabilityExecutionService:
    """Plan a capability request and execute the resulting plan."""

    def __init__(
        self,
        planner,
        executor,
        validator=None,
    ):
        self._planner = planner
        self._executor = executor
        self._validator = validator or PlanValidator()

    def execute(
        self,
        requirement: ValidationRequirement,
        inputs: Mapping[str, Any],
        execution_id: str,
    ) -> dict[str, Any]:
        plan = self._planner.plan(requirement)
        self._validator.validate(
            plan,
            self._executor.registry,
        )

        result = self._executor.execute(
            plan=plan,
            inputs=inputs,
            execution_id=execution_id,
        )
        return result


__all__ = ["CapabilityExecutionService"]