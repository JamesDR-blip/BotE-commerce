"""Serialization helpers for execution plans."""
from __future__ import annotations

from typing import Any

from domain.plans import ExecutionPlan, PlanStep


class ExecutionPlanSerializer:
    """Serialize and deserialize ExecutionPlan domain objects."""

    @staticmethod
    def to_dict(plan: ExecutionPlan) -> dict[str, Any]:
        return {
            "version": plan.version,
            "steps": [
                {
                    "capability_id": step.capability_id,
                    "capability_version": step.capability_version,
                    "parameters": step.parameters,
                    "input_mapping": step.input_mapping,
                }
                for step in plan.steps
            ],
            "metadata": plan.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ExecutionPlan:
        steps = tuple(
            PlanStep(
                capability_id=step["capability_id"],
                capability_version=step["capability_version"],
                parameters=step.get("parameters", {}),
                input_mapping=step.get("input_mapping", {}),
            )
            for step in data.get("steps", [])
        )

        return ExecutionPlan(
            steps=steps,
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
        )