from capabilities.validation import ValidationCapability
from configs.settings import Settings
from services.container import Container


def test_container_registers_validation_capability():
    container = Container(Settings())

    assert container.capabilities.has("data.clean")
    assert container.capabilities.has("data.validate")

    capability = container.capabilities.get("data.validate")

    assert isinstance(capability, ValidationCapability)
    assert capability.spec.id == "data.validate"


def test_capability_registry_is_separate_from_validator_registry():
    container = Container(Settings())

    assert container.capabilities is not container.registry


def test_container_exposes_capability_executor():
    container = Container(Settings())

    assert container.capability_executor is not None


def test_container_executor_uses_capability_registry():
    container = Container(Settings())

    capability = container.capabilities.get("data.validate")

    assert container.capability_executor is not None
    assert capability.spec.id == "data.validate"