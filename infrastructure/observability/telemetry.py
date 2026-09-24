"""Application telemetry primitives for S25 observability."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
except ImportError:  # pragma: no cover - dependency availability
    OTLPMetricExporter = None  # type: ignore[assignment]

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
except ImportError:  # pragma: no cover - dependency availability
    OTLPSpanExporter = None  # type: ignore[assignment]

from prometheus_client import Counter, Histogram


SERVICE_NAME = "ai-data-studio"

workflow_executions_total = Counter(
    "ai_studio_workflow_executions_total",
    "Total workflow executions by terminal outcome.",
    ("status",),
)

workflow_execution_duration_seconds = Histogram(
    "ai_studio_workflow_execution_duration_seconds",
    "Workflow execution duration in seconds.",
)

capability_executions_total = Counter(
    "ai_studio_capability_executions_total",
    "Total capability executions by terminal outcome.",
    ("status",),
)

capability_execution_duration_seconds = Histogram(
    "ai_studio_capability_execution_duration_seconds",
    "Capability execution duration in seconds.",
)

_governance_outcomes_total = Counter(
    "ai_studio_governance_outcomes_total",
    "Governance outcomes by boundary and outcome.",
    ("boundary", "outcome"),
)

_telemetry_configured = False


def configure_telemetry() -> None:
    """Configure process-wide OpenTelemetry tracing and metrics once."""

    global _telemetry_configured

    if _telemetry_configured:
        return

    resource = Resource.create(
        {
            "service.name": os.getenv(
                "OTEL_SERVICE_NAME",
                SERVICE_NAME,
            )
        }
    )

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    trace_provider = trace.get_tracer_provider()

    if not isinstance(trace_provider, TracerProvider):
        trace_provider = TracerProvider(resource=resource)

        if endpoint and OTLPSpanExporter is not None:
            trace_provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=endpoint)
                )
            )

        trace.set_tracer_provider(trace_provider)

    metric_provider = metrics.get_meter_provider()

    if not isinstance(metric_provider, MeterProvider):
        if endpoint and OTLPMetricExporter is not None:
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint)
            )
            metric_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
        else:
            metric_provider = MeterProvider(
                resource=resource,
            )

        metrics.set_meter_provider(metric_provider)

    _telemetry_configured = True


def tracer(name: str):
    """Return a tracer without exposing OTel to domain/application layers."""
    return trace.get_tracer(name)


def record_governance_outcome(
    *,
    boundary: str,
    outcome: str,
) -> None:
    """Record a low-cardinality governance outcome."""
    _governance_outcomes_total.labels(
        boundary=boundary,
        outcome=outcome,
    ).inc()


@contextmanager
def workflow_span(
    *,
    workflow_id: str,
    execution_id: str,
) -> Iterator[object]:
    with tracer(__name__).start_as_current_span(
        "workflow.execute"
    ) as span:
        span.set_attribute("workflow.id", workflow_id)
        span.set_attribute("execution.id", execution_id)
        yield span


def record_workflow_state_transition(
    *,
    workflow_id: str,
    execution_id: str,
    from_state: str,
    to_state: str,
) -> None:
    """Record a workflow execution state transition without payload data."""
    with tracer(__name__).start_as_current_span(
        "workflow.state_transition"
    ) as span:
        span.set_attribute("workflow.id", workflow_id)
        span.set_attribute("execution.id", execution_id)
        span.set_attribute("from_state", from_state)
        span.set_attribute("to_state", to_state)
