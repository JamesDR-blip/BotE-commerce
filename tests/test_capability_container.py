from capabilities.validation import ValidationCapability
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
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


def test_container_registers_cleaning_capability():
    container = Container(Settings())

    assert container.capabilities.has("data.clean")

    capability = container.capabilities.get("data.clean")

    assert isinstance(capability, CleaningCapability)
    assert capability.spec.id == "data.clean"


def test_container_registers_extraction_capability():
    container = Container(Settings())

    assert container.capabilities.has("data.extract")

    capability = container.capabilities.get("data.extract")

    assert isinstance(capability, ExtractionCapability)
    assert capability.spec.id == "data.extract"


def test_container_planner_catalog_matches_capability_registry():
    container = Container(Settings())

    registry_catalog = container.capabilities.catalog()

    assert container.planner._catalog == registry_catalog