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
    required_input_keys: tuple[str, ...] | None = None

    required_capabilities: tuple[
        str | CapabilityDependency,
        ...
    ] = ()
    parameter_keys: tuple[str, ...] = ()

    parameter_keywords: Mapping[
        str,
        Mapping[str, tuple[str, ...]]
    ] = field(
        default_factory=dict
    )
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

        mapping_targets = [
            target
            for target, _ in self.input_mappings
        ]

        unknown_mapping_targets = (
            set(mapping_targets)
            - set(self.input_keys)
        )

        if unknown_mapping_targets:
            raise ValueError(
                f"Input mapping references unknown input "
                f"keys for {self.id}: "
                f"{sorted(unknown_mapping_targets)}"
            )

        if len(mapping_targets) != len(set(mapping_targets)):
            raise ValueError(
                f"Duplicate input mapping target "
                f"for {self.id}"
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

        unknown_parameter_keywords = (
            set(self.parameter_keywords)
            -
            set(self.parameter_keys)
        )

        if unknown_parameter_keywords:
            raise ValueError(
                f"Parameter keywords reference unknown parameters "
                f"for {self.id}: "
                f"{sorted(unknown_parameter_keywords)}"
            )

        input_mapping_inputs = [
            input_key
            for input_key, _ in self.input_mappings
        ]

        unknown_mapping_inputs = (
            set(input_mapping_inputs)
            - set(self.input_keys)
        )

        if unknown_mapping_inputs:
            raise ValueError(
                f"Input mapping references unknown input "
                f"keys for {self.id}: "
                f"{sorted(unknown_mapping_inputs)}"
            )

        if len(input_mapping_inputs) != len(
            set(input_mapping_inputs)
        ):
            raise ValueError(
                f"Duplicate input mapping for {self.id}"
            )

        required_inputs = (
            self.input_keys
            if self.required_input_keys is None
            else self.required_input_keys
        )

        object.__setattr__(
            self,
            "required_input_keys",
            tuple(required_inputs),
        )

        unknown_required_inputs = (
            set(self.required_input_keys)
            - set(self.input_keys)
        )

        if unknown_required_inputs:
            raise ValueError(
                f"Required input keys reference unknown "
                f"inputs for {self.id}: "
                f"{sorted(unknown_required_inputs)}"
            )

        if len(self.required_input_keys) != len(
            set(self.required_input_keys)
        ):
            raise ValueError(
                f"Duplicate required input key "
                f"for {self.id}"
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