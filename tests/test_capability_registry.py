import pytest

from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.capability_registry import CapabilityRegistry
from domain.exceptions import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotFoundError,
)


class EchoCapability:
    def __init__(self, capability_id: str) -> None:
        self._spec = CapabilitySpec(
            id=capability_id,
            version="1.0",
            description="Test capability",
            input_keys=("value",),
            output_keys=("value",),
        )

    @property
    def spec(self) -> CapabilitySpec:
        return self._spec

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        return CapabilityResult(
            outputs={"value": context.inputs["value"]}
        )


def test_register_and_resolve_capability():
    registry = CapabilityRegistry()
    capability = EchoCapability("test.echo")

    registry.register(capability)

    assert registry.has("test.echo")
    assert registry.get("test.echo") is capability


def test_unknown_capability_raises():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotFoundError):
        registry.get("does.not.exist")


def test_duplicate_capability_id_is_rejected():
    registry = CapabilityRegistry()

    registry.register(EchoCapability("test.echo"))

    with pytest.raises(CapabilityAlreadyRegisteredError):
        registry.register(EchoCapability("test.echo"))


def test_list_returns_registered_capabilities():
    registry = CapabilityRegistry()

    first = EchoCapability("test.first")
    second = EchoCapability("test.second")

    registry.register(first)
    registry.register(second)

    capabilities = registry.list()

    assert capabilities == (first, second)