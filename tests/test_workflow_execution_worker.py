from __future__ import annotations

import json
from types import SimpleNamespace

from execution.workflow.engine import WorkflowExecutionWorker


class FakeExecutions:
    def __init__(self, record) -> None:
        self.record = record
        self.claim_calls: list[str] = []
        self.fail_calls: list[tuple[str, str]] = []

    def claim_running(self, execution_id: str):
        self.claim_calls.append(execution_id)
        return self.record

    def fail(self, *, execution_id: str, error: str):
        self.fail_calls.append((execution_id, error))


class FakeEngine:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.executed: list[str] = []

    def execute_existing(self, execution_id: str):
        self.executed.append(execution_id)
        if self.error is not None:
            raise self.error


def test_worker_claims_then_executes_persisted_execution() -> None:
    executions = FakeExecutions(
        SimpleNamespace(
            id="execution-1",
            status="RUNNING",
        )
    )
    engine = FakeEngine()

    worker = WorkflowExecutionWorker(
        executions=executions,
        workflow_engine=engine,
    )

    worker.run("execution-1")

    assert executions.claim_calls == ["execution-1"]
    assert engine.executed == ["execution-1"]
    assert executions.fail_calls == []


def test_worker_does_not_execute_when_claim_fails() -> None:
    class UnclaimableExecutions(FakeExecutions):
        def claim_running(self, execution_id: str):
            self.claim_calls.append(execution_id)
            return None

    executions = UnclaimableExecutions(None)
    engine = FakeEngine()

    worker = WorkflowExecutionWorker(
        executions=executions,
        workflow_engine=engine,
    )

    worker.run("execution-1")

    assert executions.claim_calls == ["execution-1"]
    assert engine.executed == []
    assert executions.fail_calls == []


def test_worker_persists_failure_when_engine_setup_fails() -> None:
    executions = FakeExecutions(
        SimpleNamespace(
            id="execution-1",
            status="RUNNING",
        )
    )
    engine = FakeEngine(
        error=ValueError("workflow version missing")
    )

    worker = WorkflowExecutionWorker(
        executions=executions,
        workflow_engine=engine,
    )

    worker.run("execution-1")

    assert engine.executed == ["execution-1"]
    assert executions.fail_calls == [
        ("execution-1", "workflow version missing")
    ]
