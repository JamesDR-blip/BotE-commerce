import pandas as pd
import pytest

from domain.models import ExecutionSummary, ValidationResult
from domain.plans import ExecutionPlan, PlanStep
from domain.capability_execution import CapabilityExecutionResult
from domain.execution_trace import ExecutionTrace

from services.quality_service import QualityService
from agents.requirement import ValidationRequirement
from .conftest import FakeExecutions

class FakeReporter:
    def generate(self, execution_id, result):
        return {"json": "report.json"}

class FakeExecutions:
    def __init__(self):
        self.created = []
        self.status_updates = []
        self.saved_context = []
        self.saved_traces = []

    def create(self, record):
        self.created.append(record)

    def update_status(self, execution_id, status):
        self.status_updates.append((execution_id, status))

    def save_result(self, **kwargs):
        pass

    def save_execution_context(
        self,
        execution_id,
        *,
        requirement_json,
        plan_json,
        planner_version,
    ):
        self.saved_context.append(
            {
                "execution_id": execution_id,
                "requirement_json": requirement_json,
                "plan_json": plan_json,
                "planner_version": planner_version,
            }
        )

    def save_trace(self, execution_id, trace):
        self.saved_traces.append(
            {
                "execution_id": execution_id,
                "trace": trace,
            }
        )

class FakeRequirements:
    def interpret(
        self,
        requested_category=None,
        requested_capabilities=(),
    ):
        return ValidationRequirement(
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
        )


class FakeAgents:
    def __init__(self):
        self.requirements = FakeRequirements()

class FakeCache:
    def get(self, key):
        return None

    def set(self, key, value):
        pass


class FakeSettings:
    enable_llm = False


class FakeContainer:
    def __init__(self):
        self.executions = FakeExecutions()
        self.agents = FakeAgents()
        self.cache = FakeCache()
        self.settings = FakeSettings()
        self.reporter = FakeReporter()

class FakeCapabilityExecution:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, requirement, inputs, execution_id):
        self.calls.append(
            {
                "requirement": requirement,
                "inputs": inputs,
                "execution_id": execution_id,
            }
        )

        if self.error is not None:
            raise self.error

        plan = ExecutionPlan(
            steps=(),
            version="1.0",
            metadata={},
        )

        trace = ExecutionTrace(
            execution_id=execution_id,
            records=(),
        )

        return CapabilityExecutionResult(
            outputs={
                "validation_result": self.result,
            },
            plan=plan,
            trace=trace,
        )

def test_quality_service_marks_execution_completed():
    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
            "size": ["42"],
            "color": ["Black"],
        }
    )

    container = FakeContainer()

    container.capability_execution = FakeCapabilityExecution(
        ValidationResult(
            category="Fashion",
            clean=frame,
            quarantine=pd.DataFrame(),
            issues=[],
            health_score=95.0,
            rule_version="1",
        )
    )

    service = make_service(container)

    result = service.validate(
        frame,
        b"source-data",
        "Fashion",
    )

    assert isinstance(result, ExecutionSummary)
    assert result.category == "Fashion"
    assert result.health_score == 95.0

    assert len(container.executions.created) == 1

    execution_id = container.executions.created[0].id

    assert container.executions.status_updates == [
        (execution_id, "COMPLETED")
    ]
    assert len(container.executions.saved_context) == 1

    context = container.executions.saved_context[0]

    assert context["execution_id"] == execution_id
    assert context["requirement_json"]
    assert context["plan_json"]
    assert context["planner_version"] is None

    assert len(container.executions.saved_traces) == 1

    saved_trace = container.executions.saved_traces[0]

    assert saved_trace["execution_id"] == execution_id
    assert saved_trace["trace"].execution_id == execution_id

def test_quality_service_marks_execution_failed_and_reraises():
    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    error = RuntimeError("workflow failed")

    container = FakeContainer()

    container.capability_execution = FakeCapabilityExecution(
        error=error
    )

    service = make_service(container)

    with pytest.raises(RuntimeError, match="workflow failed"):
        service.validate(
            frame,
            b"source-data",
            "Fashion",
        )

    assert len(container.executions.created) == 1

    execution_id = container.executions.created[0].id

    assert container.executions.status_updates == [
        (execution_id, "FAILED")
    ]


def test_quality_service_uses_capability_execution_service():
    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
            "size": ["42"],
            "color": ["Black"],
        }
    )

    validation_result = ValidationResult(
        category="Fashion",
        clean=frame,
        quarantine=pd.DataFrame(),
        issues=[],
        health_score=95.0,
        rule_version="1",
    )

    container = FakeContainer()

    capability_execution = FakeCapabilityExecution(
        validation_result
    )

    container.capability_execution = capability_execution

    service = make_service(container)

    result = service.validate(
        frame,
        b"source-data",
        "Fashion",
    )

    assert result.category == "Fashion"
    assert result.health_score == 95.0

    assert len(capability_execution.calls) == 1

    call = capability_execution.calls[0]

    assert call["inputs"]["frame"] is frame
    assert call["inputs"]["requested_category"] == "Fashion"
    assert call["execution_id"]


def make_service(container):
    return QualityService(
        requirements=container.agents.requirements,
        capability_execution=container.capability_execution,
        executions=container.executions,
        cache=container.cache,
        reporter=container.reporter,
        enable_llm=container.settings.enable_llm,
    )