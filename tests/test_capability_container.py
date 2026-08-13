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


def test_container_planner_uses_capability_registry():
    container = Container(Settings())

    assert container.planner._registry is container.capabilities


def test_container_planner_catalog_is_derived_from_registry():
    container = Container(Settings())

    assert (
        container.planner._registry.catalog()
        == container.capabilities.catalog()
    )


def test_container_planner_sees_registered_capabilities():
    container = Container(Settings())

    registered_ids = {
        capability.spec.id
        for capability in container.capabilities.list()
    }

    planner_ids = set(
        container.planner._registry.catalog()
    )

    assert planner_ids == registered_ids


def test_container_planner_sees_capability_registered_after_creation():
    from domain.capabilities import CapabilityResult, CapabilitySpec
    from agents.requirement import ValidationRequirement

    class LateCapability:
        spec = CapabilitySpec(
            id="test.late",
            version="1.0",
            description="Late registered capability",
            input_keys=(),
            output_keys=("result",),
        )

        def execute(self, context):
            return CapabilityResult(
                outputs={"result": "late"},
            )

    container = Container(Settings())

    container.capabilities.register(LateCapability())

    plan = container.planner.plan(
        ValidationRequirement(
            requested_capabilities=("test.late",),
        )
    )

    assert [
        step.capability_id
        for step in plan.steps
    ] == ["test.late"]