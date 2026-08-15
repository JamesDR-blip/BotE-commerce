from __future__ import annotations

from collections.abc import Mapping


class IntentResolver:
    """
    Resolve business intents into capability identifiers.
    """

    def __init__(
        self,
        intent_mapping: Mapping[str, tuple[str, ...]],
    ) -> None:
        self._mapping = dict(intent_mapping)

    @classmethod
    def from_registry(
        cls,
        registry,
    ) -> "IntentResolver":
        """
        Build intent mapping dynamically from registered capabilities.
        """

        mapping: dict[str, list[str]] = {}

        for spec in registry.specs():
            for intent in spec.intents:
                mapping.setdefault(
                    intent,
                    [],
                ).append(
                    spec.id
                )

        return cls(
            {
                intent: tuple(capabilities)
                for intent, capabilities
                in mapping.items()
            }
        )

    def resolve(
        self,
        intents: tuple[str, ...],
    ) -> tuple[str, ...]:

        capabilities: list[str] = []

        for intent in intents:
            if intent not in self._mapping:
                raise ValueError(
                    f"Unknown intent: {intent}"
                )

            for capability in self._mapping[intent]:
                if capability not in capabilities:
                    capabilities.append(capability)

        return tuple(capabilities)