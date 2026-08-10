from capabilities.validation import ValidationCapability
from configs.settings import Settings
from services.container import Container


def test_container_registers_validation_capability():
    container = Container(Settings())

    assert container.capabilities.has("data.validate")

    capability = container.capabilities.get("data.validate")

    assert isinstance(capability, ValidationCapability)
    assert capability.spec.id == "data.validate"


def test_capability_registry_is_separate_from_validator_registry():
    container = Container(Settings())

    assert container.capabilities is not container.registry