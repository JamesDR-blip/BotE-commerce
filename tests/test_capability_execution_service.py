from dataclasses import dataclass

from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.capability_registry import CapabilityRegistry
from domain.dependency_resolver import DependencyResolver
from services.capability_execution_service import CapabilityExecutionService
from services.capability_executor import CapabilityExecutor


@dataclass
class EchoCapability:
    spec = CapabilitySpec(
        id="test.echo",
        version="1.0",
        description="Echo input",
        input_keys=("value",),
        output_keys=("echo",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "echo": context.inputs["value"],
            }
        )


def test_execution_service_plans_then_executes():
    registry = CapabilityRegistry()
    registry.register(EchoCapability())

    planner = PlannerAgent(
        catalog={
            "test.echo": EchoCapability.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.echo",),
    )

    result = service.execute(
        requirement=requirement,
        inputs={"value": "hello"},
        execution_id="execution-123",
    )

    assert result["echo"] == "hello"


@dataclass
class CleanCapability:
    spec = CapabilitySpec(
        id="test.clean",
        version="1.0",
        description="Clean input",
        input_keys=("value",),
        output_keys=("value",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "value": context.inputs["value"].strip(),
            }
        )

@dataclass
class ValidateCapability:
    spec = CapabilitySpec(
        id="test.validate",
        version="1.0",
        description="Validate cleaned input",
        input_keys=("value",),
        output_keys=("valid",),
        required_capabilities=("test.clean",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "valid": context.inputs["value"] == "hello",
            }
        )


def test_execution_service_executes_multiple_capabilities_in_plan():
    registry = CapabilityRegistry()

    clean = CleanCapability()
    validate = ValidateCapability()

    registry.register(clean)
    registry.register(validate)

    planner = PlannerAgent(
        catalog={
            clean.spec.id: clean.spec,
            validate.spec.id: validate.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "test.validate",
        ),
    )

    result = service.execute(
        requirement=requirement,
        inputs={"value": " hello "},
        execution_id="execution-123",
    )

    assert result["value"] == "hello"
    assert result["valid"] is True


def test_execution_service_resolves_capability_dependencies():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ValidateCapability())

    planner = PlannerAgent(
        catalog={
            "test.clean": CleanCapability.spec,
            "test.validate": ValidateCapability.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.validate",),
    )

    result = service.execute(
        requirement=requirement,
        inputs={"value": "  hello  "},
        execution_id="execution-123",
    )

    assert result["value"] == "hello"
    assert result["valid"] is True


def test_execution_service_executes_dependencies_before_requested_capability():
    registry = CapabilityRegistry()

    clean = CleanCapability()
    validate = ValidateCapability()

    registry.register(clean)
    registry.register(validate)

    planner = PlannerAgent(
        catalog={
            clean.spec.id: clean.spec,
            validate.spec.id: validate.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.validate",),
    )

    result = service.execute(
        requirement=requirement,
        inputs={"value": " hello "},
        execution_id="execution-123",
    )

    assert result["value"] == "hello"
    assert result["valid"] is True


@dataclass
class RenameCleanCapability:
    spec = CapabilitySpec(
        id="test.rename_clean",
        version="1.0",
        description="Clean input and rename output",
        input_keys=("value",),
        output_keys=("cleaned_value",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "cleaned_value": context.inputs["value"].strip(),
            }
        )


@dataclass
class RenameValidateCapability:
    spec = CapabilitySpec(
        id="test.rename_validate",
        version="1.0",
        description="Validate renamed cleaned input",
        input_keys=("value",),
        output_keys=("valid",),
        required_capabilities=("test.rename_clean",),
        input_mappings=(
            ("value", "cleaned_value"),
        ),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "valid": context.inputs["value"] == "hello",
            }
        )


def test_execution_service_uses_explicit_mapping_between_renamed_outputs_and_inputs():
    registry = CapabilityRegistry()

    clean = RenameCleanCapability()
    validate = RenameValidateCapability()

    registry.register(clean)
    registry.register(validate)

    planner = PlannerAgent(
        catalog={
            clean.spec.id: clean.spec,
            validate.spec.id: validate.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.rename_validate",),
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "test.rename_clean",
        "test.rename_validate",
    ]

    assert plan.steps[1].input_mapping == {
        "value": "cleaned_value",
    }

    result = service.execute(
        requirement=requirement,
        inputs={"value": " hello "},
        execution_id="explicit-mapping-test",
    )

    assert result["cleaned_value"] == "hello"
    assert result["valid"] is True



@dataclass
class FormatCapability:
    spec = CapabilitySpec(
        id="test.format",
        version="1.0",
        description="Format a value with a configurable prefix",
        input_keys=("value",),
        output_keys=("formatted",),
        parameter_keys=("prefix",),
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={
                "formatted": (
                    f"{context.config['prefix']}"
                    f"{context.inputs['value']}"
                ),
            }
        )


def test_new_capability_is_plannable_and_executable_without_core_changes():
    registry = CapabilityRegistry()

    capability = FormatCapability()
    registry.register(capability)

    planner = PlannerAgent(
        catalog={
            capability.spec.id: capability.spec,
        },
        resolver=DependencyResolver(),
    )

    executor = CapabilityExecutor(registry)

    service = CapabilityExecutionService(
        planner=planner,
        executor=executor,
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.format",),
        parameters={
            "test.format": {
                "prefix": "SKU-",
            },
        },
    )

    plan = planner.plan(requirement)

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == "test.format"
    assert plan.steps[0].capability_version == "1.0"
    assert plan.steps[0].parameters == {
        "prefix": "SKU-",
    }

    result = service.execute(
        requirement=requirement,
        inputs={"value": "12345"},
        execution_id="extensibility-test",
    )

    assert result["formatted"] == "SKU-12345"