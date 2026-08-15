"""Interpret validation requests without invoking executable LLM output."""
from __future__ import annotations

from dataclasses import dataclass
from agents.intent_classifier import IntentClassifier


@dataclass(frozen=True)
class ValidationRequirement:
    """The validated user intent available to the orchestration graph."""

    requested_category: str | None = None

    requested_capabilities: tuple[str, ...] = ()

    requested_intents: tuple[str, ...] = ()

    input_mappings: dict[str, dict[str, str]] | None = None

    parameters: dict[str, dict[str, object]] | None = None


class RequirementAgent:
    """Convert transport input into typed workflow requirement."""

    def __init__(
        self,
        classifier: IntentClassifier | None = None,
    ) -> None:
        self._classifier = classifier

    def interpret(
        self,
        requested_category: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        requested_intents: tuple[str, ...] = (),
        input_mappings: dict[str, dict[str, str]] | None = None,
        parameters: dict[str, dict[str, object]] | None = None,
        user_request: str | None = None,
    ) -> ValidationRequirement:

        if (
            not requested_intents
            and user_request
            and self._classifier
        ):
            requested_intents = (
                self._classifier.classify(
                    user_request
                )
            )

        return ValidationRequirement(
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
            requested_intents=requested_intents,
            input_mappings=input_mappings,
            parameters=parameters,
        )