from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from domain.capability_dependency import CapabilityDependency

@dataclass(frozen=True)
class CapabilitySpec:
    """Static contract describing a capability."""

    id: str
    version: str
    description: str

    input_keys: tuple[str, ...]
    output_keys: tuple[str, ...]

    required_capabilities: tuple[
        str | CapabilityDependency,
        ...
    ] = ()
    parameter_keys: tuple[str, ...] = ()
    input_mappings: tuple[tuple[str, str], ...] = ()

    input_types: Mapping[str, type] = field(
        default_factory=dict
    )

    output_types: Mapping[str, type] = field(
        default_factory=dict
    )

    intents: tuple[str, ...] = ()

@dataclass(frozen=True)
class CapabilityContext:
    """Runtime context supplied to a capability."""

    execution_id: str
    inputs: Mapping[str, Any]
    config: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityResult:
    """Normalized result returned by a capability."""

    outputs: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Capability(Protocol):
    """Execution contract implemented by every capability."""

    @property
    def spec(self) -> CapabilitySpec:
        ...

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        ...