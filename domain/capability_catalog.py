from __future__ import annotations

from typing import Mapping

from domain.capabilities import CapabilitySpec


def build_capability_catalog(
    specs: tuple[CapabilitySpec, ...],
) -> Mapping[str, CapabilitySpec]:
    """Build an immutable-by-convention capability lookup catalog."""
    return {
        spec.id: spec
        for spec in specs
    }