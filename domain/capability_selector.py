"""Deterministic selection of requested capabilities."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.requirement import ValidationRequirement


CapabilityCatalog = (
    Iterable[str]
    | Callable[[], Iterable[str]]
)


class CapabilitySelector:
    """Resolve explicitly requested capabilities against a capability catalog."""

    def __init__(
        self,
        available_capabilities: CapabilityCatalog,
    ) -> None:
        self._available_capabilities = available_capabilities

    def _available(self) -> frozenset[str]:
        available = self._available_capabilities

        if callable(available):
            available = available()

        return frozenset(available)

    def select(
        self,
        requirement: ValidationRequirement,
    ) -> tuple[str, ...]:
        selected = requirement.requested_capabilities
        available = self._available()

        unknown = [
            capability_id
            for capability_id in selected
            if capability_id not in available
        ]

        if unknown:
            raise ValueError(
                "Unknown capability: "
                + ", ".join(unknown)
            )

        return selected