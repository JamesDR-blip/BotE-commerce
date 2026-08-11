from __future__ import annotations

from domain.capabilities import Capability, CapabilitySpec
from domain.exceptions import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotFoundError,
)



class CapabilityRegistry:
    """Registry for resolving capabilities by their specification ID."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        capability_id = capability.spec.id

        if capability_id in self._capabilities:
            raise CapabilityAlreadyRegisteredError(
                f"Capability already registered: {capability_id}"
            )

        self._capabilities[capability_id] = capability

    def get(self, capability_id: str) -> Capability:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise CapabilityNotFoundError(
                f"Capability not found: {capability_id}"
            ) from exc

    def has(self, capability_id: str) -> bool:
        return capability_id in self._capabilities

    def list(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities.values())

    def specs(self) -> tuple[CapabilitySpec, ...]:
        """Return the static specifications of all registered capabilities."""
        return tuple(
            capability.spec
            for capability in self._capabilities.values()
        )

    def catalog(self) -> dict[str, CapabilitySpec]:
        """Return registered capability specifications keyed by ID."""
        return {
            capability.spec.id: capability.spec
            for capability in self._capabilities.values()
        }