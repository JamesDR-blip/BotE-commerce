from __future__ import annotations

from collections.abc import Mapping

from agents.intent_classifier import IntentClassifier
from agents.parameter_resolver import ParameterResolver
from domain.capabilities import CapabilitySpec
from domain.intent_resolver import IntentResolver


class RequirementInterpreter:
    """
    Convert user request into structured requirement information.
    """

    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        intent_resolver: IntentResolver | None = None,
        parameter_resolver: ParameterResolver | None = None,
        catalog: Mapping[str, CapabilitySpec] | None = None,
    ) -> None:

        self._classifier = classifier
        self._intent_resolver = intent_resolver
        self._parameter_resolver = parameter_resolver
        self._catalog = catalog or {}

    def interpret(
        self,
        user_request: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        requested_intents: tuple[str, ...] = (),
        parameters: dict[str, dict[str, object]] | None = None,
    ) -> tuple[
        tuple[str, ...],
        tuple[str, ...],
        dict[str, dict[str, object]] | None,
    ]:

        if (
            not requested_intents
            and user_request
            and self._classifier
        ):
            requested_intents = self._classifier.classify(
                user_request
            )

        if (
            not requested_capabilities
            and requested_intents
            and self._intent_resolver
        ):
            requested_capabilities = (
                self._intent_resolver.resolve(
                    requested_intents
                )
            )

        if (
            parameters is None
            and user_request
            and requested_capabilities
            and self._parameter_resolver
        ):
            parameters = (
                self._parameter_resolver.resolve(
                    text=user_request,
                    capabilities=requested_capabilities,
                    catalog=self._catalog,
                )
            )

        return (
            requested_capabilities,
            requested_intents,
            parameters,
        )