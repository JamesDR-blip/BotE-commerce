from __future__ import annotations

from domain.capabilities import Capability
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