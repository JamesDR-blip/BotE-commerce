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