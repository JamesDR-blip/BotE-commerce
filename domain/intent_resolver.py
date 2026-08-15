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