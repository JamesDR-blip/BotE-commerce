"""Interpret validation requests without invoking executable LLM output."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationRequirement:
    """The validated user intent available to the orchestration graph."""

    requested_category: str | None = None
    requested_capabilities: tuple[str, ...] = ()
    input_mappings: dict[str, dict[str, str]] | None = None
    parameters: dict[str, dict[str, object]] | None = None

class RequirementAgent:
    """Convert the current transport input into a typed workflow requirement."""

    def interpret(
        self,
        requested_category: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        input_mappings: dict[str, dict[str, str]] | None = None,
        parameters: dict[str, dict[str, object]] | None = None,
    ) -> ValidationRequirement:
        return ValidationRequirement(
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
            input_mappings=input_mappings,
            parameters=parameters,
        )
