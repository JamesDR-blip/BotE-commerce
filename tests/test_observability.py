from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app
from configs.settings import Settings


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_url="sqlite://",
                reports_path=tmp_path / "reports",
            )
        ),
        raise_server_exceptions=False,
    )


def test_metrics_exposes_workflow_execution_metrics(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "ai_studio_workflow_executions_total" in body
    assert "ai_studio_workflow_execution_duration_seconds" in body
import json

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from domain.plans import ExecutionPlan
from execution.workflow.engine import WorkflowEngine
from domain.capability_execution import CapabilityExecutionResult
from domain.execution_trace import ExecutionTrace


class _FakeWorkflow:
    def get(self, workflow_id):
        return object()

    def get_active_version(self, workflow_id):
        class Version:
            version = "1.0"
            plan_json = json.dumps(
                {
                    "version": "1.0",
                    "steps": [],
                    "metadata": {},
                }
            )

        return Version()


class _FakeCapabilityExecution:
    def execute_plan(self, **kwargs):
        plan = kwargs["plan"]
        return CapabilityExecutionResult(
            outputs={"result": "ok"},
            plan=plan,
            trace=ExecutionTrace(
                execution_id=kwargs["execution_id"],
                records=(),
            ),
        )


def test_workflow_execution_creates_otel_span() -> None:
    from opentelemetry import trace

    exporter = InMemorySpanExporter()

    from infrastructure.observability.telemetry import configure_telemetry

    configure_telemetry()

    provider = trace.get_tracer_provider()

    assert isinstance(provider, TracerProvider)

    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )

    engine = WorkflowEngine(
        workflows=_FakeWorkflow(),
        capability_execution=_FakeCapabilityExecution(),
    )

    runtime = engine.execute(
        workflow_id="wf-observability",
        execution_id="exec-observability",
        inputs={"value": "test"},
    )

    assert runtime.success is True

    spans = exporter.get_finished_spans()

    workflow_spans = [
        span
        for span in spans
        if span.name == "workflow.execute"
    ]

    assert len(workflow_spans) == 1

    span = workflow_spans[0]

    assert span.attributes["execution.id"] == (
        "exec-observability"
    )
    assert span.attributes["workflow.id"] == (
        "wf-observability"
    )
    assert span.attributes["plan.step_count"] == 0

def test_workflow_state_transition_creates_safe_otel_span() -> None:
    from opentelemetry import trace

    from infrastructure.observability.telemetry import (
        configure_telemetry,
        record_workflow_state_transition,
    )

    exporter = InMemorySpanExporter()

    configure_telemetry()

    provider = trace.get_tracer_provider()

    assert isinstance(provider, TracerProvider)

    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )

    record_workflow_state_transition(
        workflow_id="wf-state-observability",
        execution_id="exec-state-observability",
        from_state="RUNNING",
        to_state="COMPLETED",
    )

    spans = exporter.get_finished_spans()

    transition_spans = [
        span
        for span in spans
        if span.name == "workflow.state_transition"
    ]

    assert len(transition_spans) == 1

    span = transition_spans[0]

    assert span.attributes["workflow.id"] == (
        "wf-state-observability"
    )
    assert span.attributes["execution.id"] == (
        "exec-state-observability"
    )
    assert span.attributes["from_state"] == "RUNNING"
    assert span.attributes["to_state"] == "COMPLETED"

    assert len(span.attributes) == 4


class _FakeCopilotModel:
    def generate_content(self, **kwargs):
        class Part:
            text = "safe response"

        class Content:
            parts = [Part()]

        class Candidate:
            content = Content()

        class Response:
            candidates = [Candidate()]

        return Response()


def test_copilot_reasoning_creates_safe_otel_span() -> None:
    from opentelemetry import trace

    from application.copilot.agent import CopilotAgent

    exporter = InMemorySpanExporter()

    from infrastructure.observability.telemetry import configure_telemetry

    configure_telemetry()

    provider = trace.get_tracer_provider()

    assert isinstance(provider, TracerProvider)

    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )

    agent = CopilotAgent(
        model=_FakeCopilotModel(),
        model_name="test-model",
        tool_registry=None,
    )

    secret_prompt = "customer@example.com confidential payload"

    result = agent.respond(secret_prompt)

    assert result.message == "safe response"

    spans = exporter.get_finished_spans()

    reasoning_spans = [
        span
        for span in spans
        if span.name == "agent.reasoning"
    ]

    assert len(reasoning_spans) == 1

    span = reasoning_spans[0]

    assert span.attributes["agent.type"] == "copilot"
    assert span.attributes["agent.operation"] == "respond"
    assert span.attributes["model.name"] == "test-model"

    attributes_text = str(dict(span.attributes))

    assert secret_prompt not in attributes_text
    assert "safe response" not in attributes_text

class _FakeCopilotModel:
    def generate_content(self, **kwargs):
        class Part:
            text = "safe response"

        class Content:
            parts = [Part()]

        class Candidate:
            content = Content()

        class Response:
            candidates = [Candidate()]

        return Response()


def test_copilot_reasoning_creates_safe_otel_span() -> None:
    from opentelemetry import trace

    from application.copilot.agent import CopilotAgent

    exporter = InMemorySpanExporter()

    from infrastructure.observability.telemetry import configure_telemetry

    configure_telemetry()

    provider = trace.get_tracer_provider()

    assert isinstance(provider, TracerProvider)

    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )

    agent = CopilotAgent(
        model=_FakeCopilotModel(),
        model_name="test-model",
        tool_registry=None,
    )

    secret_prompt = "customer@example.com confidential payload"

    result = agent.respond(secret_prompt)

    assert result.message == "safe response"

    spans = exporter.get_finished_spans()

    reasoning_spans = [
        span
        for span in spans
        if span.name == "agent.reasoning"
    ]

    assert len(reasoning_spans) == 1

    span = reasoning_spans[0]

    assert span.attributes["agent.type"] == "copilot"
    assert span.attributes["agent.operation"] == "respond"
    assert span.attributes["model.name"] == "test-model"

    attributes_text = str(dict(span.attributes))

    assert secret_prompt not in attributes_text
    assert "safe response" not in attributes_text

