from types import SimpleNamespace
from domain.capabilities import (
    CapabilitySpec,
)
from agents.requirement import ValidationRequirement
from domain.plans import ExecutionPlan
from domain.execution_trace import ExecutionTrace
from domain.capability_execution import CapabilityExecutionResult

class FakeTraces:
    def list_by_execution(self, execution_id):
        return [
            SimpleNamespace(
                capability_id="data.clean",
                capability_version="1.0",
                status="COMPLETED",
                started_at=None,
                finished_at=None,
            )
        ]
    
class FakeCapability:
    def __init__(self, spec: CapabilitySpec) -> None:
        self._spec = spec

    @property
    def spec(self) -> CapabilitySpec:
        return self._spec

    def execute(self, context):
        raise NotImplementedError

class FakeClassifier:
    def classify(
        self,
        frame,
        categories,
        requested_category=None,
    ):
        return requested_category or "Fashion"

class FakeFixer:
    def fix(self, frame, validator):
        return frame.assign(cleaned=True)


class FakeRegistry:
    def categories(self):
        return ("Fashion",)

    def get(self, category):
        return object()


class FakeReporter:
    def generate(self, execution_id, result):
        return {"json": "report.json"}

class FakeExecutions:

    def __init__(self, context=None):
        self.context = context

        self.execution = SimpleNamespace(
            id="exec-1",
            workflow_id="wf-1",
            workflow_version="1.0",
            status="COMPLETED",
            category="electronics",
            health_score=95.0,
            created_at=None,
            requirement_json=None,
            plan_json=None,
            planner_version=None,
        )

        self.created = []
        self.status_updates = []
        self.saved_traces = []

    def get(self, execution_id):
        if execution_id != self.execution.id:
            return None

        return self.execution

    def create(self, record):
        self.created.append(record)

    def execution_context(self, execution_id):
        if self.context is None:
            return None

        return self.context

    def update_status(
        self,
        execution_id,
        status,
    ):
        self.status_updates.append(
            (execution_id, status)
        )

    def save_result(self, **kwargs):
        pass

    def save_trace(self, execution_id, trace):
        self.saved_traces.append(
            {
                "execution_id": execution_id,
                "trace": trace,
            }
        )

class FakeWorkflowExecutions:
    def __init__(self):
        self.execution = SimpleNamespace(
            id="wf-exec-1",
            workflow_id="wf-1",
            workflow_version="1.0",
            status="COMPLETED",
            inputs_json='{"file":"products.csv"}',
            outputs_json='{"file":"products.csv"}',
            error=None,
            created_at=None,
            started_at=None,
            finished_at=None,
        )

    def get(self, execution_id):
        if execution_id == self.execution.id:
            return self.execution

        return None

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