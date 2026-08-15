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

    intent_keywords: Mapping[
        str,
        tuple[str, ...]
    ] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "Capability id cannot be empty"
            )

        if not self.version.strip():
            raise ValueError(
                f"Capability version missing: {self.id}"
            )

        if len(set(self.input_keys)) != len(self.input_keys):
            raise ValueError(
                f"Duplicate input key in capability: {self.id}"
            )

        if len(set(self.output_keys)) != len(self.output_keys):
            raise ValueError(
                f"Duplicate output key in capability: {self.id}"
            )

        unknown_input_types = (
            set(self.input_types)
            - set(self.input_keys)
        )

        if unknown_input_types:
            raise ValueError(
                f"Input types reference unknown keys "
                f"for {self.id}: "
                f"{sorted(unknown_input_types)}"
            )

        unknown_output_types = (
            set(self.output_types)
            - set(self.output_keys)
        )

        if unknown_output_types:
            raise ValueError(
                f"Output types reference unknown keys "
                f"for {self.id}: "
                f"{sorted(unknown_output_types)}"
            )

        unknown_intent_keywords = (
            set(self.intent_keywords)
            -
            set(self.intents)
        )

        if unknown_intent_keywords:
            raise ValueError(
                f"Intent keywords reference unknown intents "
                f"for {self.id}: "
                f"{sorted(unknown_intent_keywords)}"
            )
        unknown_intents = (
            set(self.intent_keywords)
            -
            set(self.intents)
        )

        if unknown_intents:
            raise ValueError(
                "Intent keywords reference unknown intents "
                f"for {self.id}: "
                f"{sorted(unknown_intents)}"
            )

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

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    success: bool = True

    error: str | None = None


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