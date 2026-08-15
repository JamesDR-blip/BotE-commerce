from typing import Protocol

from domain.capabilities import CapabilitySpec


class CapabilityCatalog(Protocol):

    def get_spec(
        self,
        capability_id: str,
    ) -> CapabilitySpec:
        ...

    def list_specs(
        self,
    ) -> tuple[CapabilitySpec, ...]:
        ...