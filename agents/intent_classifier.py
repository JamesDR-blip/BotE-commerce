from __future__ import annotations

from domain.capability_registry import CapabilityRegistry


class IntentClassifier:
    """
    Deterministic classifier mapping user text
    into business intents.
    """

    def __init__(
        self,
        intent_keywords: dict[str, tuple[str, ...]],
    ) -> None:
        self._intent_keywords = intent_keywords

    def classify(
        self,
        text: str,
    ) -> tuple[str, ...]:

        normalized = text.lower()

        intents: list[str] = []

        for intent, keywords in self._intent_keywords.items():
            if any(
                keyword.lower() in normalized
                for keyword in keywords
            ):
                intents.append(intent)

        return tuple(intents)

    @classmethod
    def from_registry(
        cls,
        registry: CapabilityRegistry,
    ) -> "IntentClassifier":

        intent_keywords: dict[
            str,
            tuple[str, ...]
        ] = {}

        for spec in registry.specs():

            for intent, keywords in (
                spec.intent_keywords.items()
            ):
                intent_keywords[intent] = keywords

        return cls(
            intent_keywords
        )