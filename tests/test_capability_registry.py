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


class FakeCapability:
    def __init__(self, spec: CapabilitySpec) -> None:
        self._spec = spec

    @property
    def spec(self) -> CapabilitySpec:
        return self._spec

    def execute(self, context):
        raise NotImplementedError


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


def test_registry_returns_capability_specs():
    registry = CapabilityRegistry()

    capability = FakeCapability(
        CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="Validate data",
            input_keys=("frame",),
            output_keys=("result",),
        )
    )

    registry.register(capability)

    specs = registry.specs()

    assert len(specs) == 1
    assert specs[0].id == "data.validate"
    assert specs[0].version == "1.0"


def test_registry_specs_returns_tuple():
    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("result",),
            )
        )
    )

    specs = registry.specs()

    assert isinstance(specs, tuple)


def test_registry_returns_capability_catalog():
    registry = CapabilityRegistry()

    validate = FakeCapability(
        CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="Validate data",
            input_keys=("frame",),
            output_keys=("result",),
        )
    )

    extract = FakeCapability(
        CapabilitySpec(
            id="data.extract",
            version="1.0",
            description="Extract data",
            input_keys=("frame",),
            output_keys=("extractions",),
        )
    )

    registry.register(validate)
    registry.register(extract)

    catalog = registry.catalog()

    assert catalog == {
        "data.validate": validate.spec,
        "data.extract": extract.spec,
    }


def test_registry_returns_capability_metadata():
    registry = CapabilityRegistry()

    capability = FakeCapability(
        CapabilitySpec(
            id="data.extract",
            version="1.0",
            description="Extract product attributes",
            input_keys=("frame",),
            output_keys=("extractions",),
            intents=(
                "extract_brand",
                "extract_color",
            ),
            
        )
    )

    registry.register(capability)

    metadata = registry.metadata()

    assert metadata == (
        {
            "id": "data.extract",
            "description": "Extract product attributes",
            "intents": (
                "extract_brand",
                "extract_color",
            ),
            "inputs": (
                "frame",
            ),
            "outputs": (
                "extractions",
            ),
        },
    )