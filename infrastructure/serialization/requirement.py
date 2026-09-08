"""Serialization helpers for workflow requirements."""
from __future__ import annotations

from typing import Any

from domain.requirement import WorkflowRequirement


class RequirementSerializer:
    """Serialize and deserialize WorkflowRequirement objects."""

    @staticmethod
    def to_dict(requirement: WorkflowRequirement) -> dict[str, Any]:
        return {
            "requested_category": requirement.requested_category,
            "requested_capabilities": list(
                requirement.requested_capabilities
            ),
            "requested_intents": list(
                requirement.requested_intents
            ),
            "input_mappings": requirement.input_mappings,
            "parameters": requirement.parameters,
        }

    @staticmethod
    def from_dict(
        data: dict[str, Any],
    ) -> WorkflowRequirement:
        return WorkflowRequirement(
            requested_category=data.get("requested_category"),
            requested_capabilities=tuple(
                data.get("requested_capabilities", ())
            ),
            requested_intents=tuple(
                data.get("requested_intents", ())
            ),
            input_mappings=data.get("input_mappings"),
            parameters=data.get("parameters"),
        )