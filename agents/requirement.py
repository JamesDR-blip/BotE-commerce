"""Interpret workflow requests without invoking executable LLM output."""
from __future__ import annotations

from dataclasses import dataclass
from agents.requirement_interpreter import RequirementInterpreter
from agents.intent_classifier import IntentClassifier
from agents.parameter_resolver import ParameterResolver
from domain.intent_resolver import IntentResolver
from domain.capabilities import CapabilitySpec
from domain.requirement import (
    ValidationRequirement,
    WorkflowRequirement,
)

from collections.abc import Mapping


class RequirementAgent:
    """Convert transport input into typed workflow requirement."""

    def __init__(
        self,
        interpreter: RequirementInterpreter | None = None,
        classifier: IntentClassifier | None = None,
        intent_resolver: IntentResolver | None = None,
        parameter_resolver: ParameterResolver | None = None,
        catalog: Mapping[str, CapabilitySpec] | None = None,
        ) -> None:
        
        if interpreter is None:
            interpreter = RequirementInterpreter(
                classifier=classifier,
                intent_resolver=intent_resolver,
                parameter_resolver=parameter_resolver,
                catalog=catalog,
            )        
        self._interpreter = interpreter

    def interpret(
        self,
        requested_category: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        requested_intents: tuple[str, ...] = (),
        input_mappings: dict[str, dict[str, str]] | None = None,
        parameters: dict[str, dict[str, object]] | None = None,
        user_request: str | None = None,
        workspace_id: str | None = None,
        user_id: str | None = None,
    ) -> WorkflowRequirement:

        if self._interpreter:
            (
                requested_capabilities,
                requested_intents,
                parameters,
            ) = self._interpreter.interpret(
                user_request=user_request,
                requested_capabilities=requested_capabilities,
                requested_intents=requested_intents,
                parameters=parameters,
                workspace_id=workspace_id,
                user_id=user_id,
            )

        return WorkflowRequirement(
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
            requested_intents=requested_intents,
            input_mappings=input_mappings,
            parameters=parameters,
        )
