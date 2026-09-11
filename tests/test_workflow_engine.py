import json

from domain.plans import ExecutionPlan

from execution.workflow.engine import WorkflowEngine

from domain.execution_trace import ExecutionTrace
from domain.capability_execution import CapabilityExecutionResult

class FakeWorkflow:

    def get(self, workflow_id):
        return object()


    def get_active_version(
        self,
        workflow_id,
    ):

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

class FakeExecutionRepository:
    def __init__(self):
        self.created = []
        self.running = []
        self.completed = []
        self.failed = []

    def create(self, **kwargs):
        self.created.append(kwargs)

    def mark_running(self, execution_id):
        self.running.append(execution_id)

    def complete(self, **kwargs):
        self.completed.append(kwargs)

    def fail(self, **kwargs):
        self.failed.append(kwargs)


class FakeCapabilityExecution:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute_plan(self, **kwargs):
        self.calls.append(kwargs)
        return self.result

class FailingCapabilityExecution:
    def execute_plan(self, **kwargs):
        raise RuntimeError(
            "capability execution failed"
        )

class FailingCapabilityExecutionWithTrace:
    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
        trace_collector,
    ):
        trace_collector.start(
            capability_id="test.failing",
            capability_version="1.0",
            inputs={"value": "input"},
        )

        raise RuntimeError(
            "capability execution failed"
        )

class FakeTracePersistence:
    def __init__(self):
        self.saved = []

    def save(self, trace):
        self.saved.append(trace)

class FailingCapabilityExecutionWithAttachedTrace:
    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
        trace_collector=None,
    ):
        from domain.execution_trace import (
            CapabilityExecutionRecord,
            ExecutionTrace,
        )
        from domain.execution_status import ExecutionStatus
        from datetime import datetime, timezone

        record = CapabilityExecutionRecord(
            capability_id="data.clean",
            capability_version="1.0",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            inputs={"file": "products.csv"},
            outputs={"cleaned": True},
        )

        trace = ExecutionTrace(
            execution_id=execution_id,
            records=(record,),
        )

        error = RuntimeError(
            "capability execution failed"
        )

        error.execution_trace = trace

        raise error

def test_workflow_engine_loads_plan():

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=None,
    )


    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv"
        },
    )


    assert runtime.workflow_id == "wf-1"

    assert runtime.workflow_version == "1.0"

    assert isinstance(
        runtime.plan,
        ExecutionPlan,
    )

    assert runtime.plan.steps == ()


def test_workflow_engine_executes_plan_and_completes():
    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    result = CapabilityExecutionResult(
        outputs={
            "result": "ok",
        },
        plan=plan,
        trace=ExecutionTrace(
            execution_id="exec-1",
            records=(),
        ),
    )

    capability_execution = FakeCapabilityExecution(
        result
    )

    executions = FakeExecutionRepository()

    trace_persistence = FakeTracePersistence()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=capability_execution,
        executions=executions,
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "value": "input",
        },
    )

    assert runtime.workflow_id == "wf-1"
    assert runtime.workflow_version == "1.0"

    assert runtime.success is True
    assert runtime.status.name == "COMPLETED"

    assert runtime.outputs == {
        "result": "ok",
    }

    assert executions.created[0][
        "execution_id"
    ] == "exec-1"

    assert executions.created[0][
        "workflow_id"
    ] == "wf-1"

    assert executions.created[0][
        "workflow_version"
    ] == "1.0"

    assert executions.running == [
        "exec-1",
    ]

    assert executions.completed[0][
        "execution_id"
    ] == "exec-1"

    assert executions.failed == []

    assert len(
        capability_execution.calls
    ) == 1

    assert (
        capability_execution.calls[0][
            "execution_id"
        ]
        == "exec-1"
    )

    assert len(
        trace_persistence.saved
    ) == 1

    saved_trace = trace_persistence.saved[0]

    assert saved_trace.execution_id == "exec-1"
    assert saved_trace.records == ()

def test_workflow_engine_marks_execution_failed():
    executions = FakeExecutionRepository()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=FailingCapabilityExecution(),
        executions=executions,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "value": "input",
        },
    )

    assert runtime.workflow_id == "wf-1"
    assert runtime.workflow_version == "1.0"

    assert runtime.success is False
    assert runtime.status.name == "FAILED"

    assert runtime.error == (
        "capability execution failed"
    )

    assert executions.created[0][
        "execution_id"
    ] == "exec-1"

    assert executions.running == [
        "exec-1",
    ]

    assert executions.completed == []

    assert executions.failed == [
        {
            "execution_id": "exec-1",
            "error": "capability execution failed",
        }
    ]

def test_workflow_engine_persists_partial_trace_on_failure():
    executions = FakeExecutionRepository()
    trace_persistence = FakeTracePersistence()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=FailingCapabilityExecutionWithTrace(),
        executions=executions,
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "value": "input",
        },
    )

    assert runtime.status.name == "FAILED"
    assert runtime.success is False
    assert runtime.error == (
        "capability execution failed"
    )

    assert executions.failed == [
        {
            "execution_id": "exec-1",
            "error": "capability execution failed",
        }
    ]

    assert len(trace_persistence.saved) == 1

    saved_trace = trace_persistence.saved[0]

    assert saved_trace.execution_id == "exec-1"
    assert len(saved_trace.records) == 1

    record = saved_trace.records[0]

    assert record.capability_id == "test.failing"
    assert record.capability_version == "1.0"

def test_workflow_engine_persists_exception_attached_trace():
    executions = FakeExecutionRepository()
    trace_persistence = FakeTracePersistence()

    engine = WorkflowEngine(
        workflows=FakeWorkflow(),
        capability_execution=(
            FailingCapabilityExecutionWithAttachedTrace()
        ),
        executions=executions,
        trace_persistence=trace_persistence,
    )

    runtime = engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "file": "products.csv",
        },
    )

    assert runtime.status.name == "FAILED"
    assert runtime.success is False

    assert runtime.error == (
        "capability execution failed"
    )

    assert len(
        trace_persistence.saved
    ) == 1

    saved_trace = (
        trace_persistence.saved[0]
    )

    assert saved_trace.execution_id == "exec-1"

    assert len(saved_trace.records) == 1

    assert (
        saved_trace.records[0].capability_id
        == "data.clean"
    )

class StreamingWorkflow:

    def get(self, workflow_id):
        return object()

    def get_active_version(self, workflow_id):
        class Version:
            version = "1.0"
            plan_json = json.dumps(
                {
                    "version": "1.0",
                    "steps": [],
                    "metadata": {
                        "execution": {
                            "mode": "streaming",
                            "chunk_size": 2,
                        },
                    },
                }
            )

        return Version()


def test_streaming_execution_requires_persisted_dataset():
    engine = WorkflowEngine(
        workflows=StreamingWorkflow(),
        capability_execution=None,
    )

    try:
        engine.execute(
            workflow_id="wf-stream",
            execution_id="exec-stream",
            inputs={},
            dataset_id=None,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Streaming workflow execution requires a dataset_id"
        )
    else:
        raise AssertionError(
            "Streaming execution must reject a missing dataset_id"
        )


class StreamingDatasetWorkflow:

    def get(self, workflow_id):
        return object()

    def get_active_version(self, workflow_id):
        class Version:
            version = "1.0"
            plan_json = json.dumps(
                {
                    "version": "1.0",
                    "steps": [],
                    "metadata": {
                        "execution": {
                            "mode": "streaming",
                            "chunk_size": 2,
                        },
                    },
                }
            )

        return Version()


class StreamingExecutionRepository:

    def create(self, **kwargs):
        self.created = kwargs

    def mark_running(self, execution_id):
        pass

    def fail(self, **kwargs):
        self.failed = kwargs

    def complete(self, **kwargs):
        self.completed = kwargs


class StreamingDatasetRepository:

    def get(self, dataset_id):
        return None


class StreamingDatasetStorage:

    def open(self, *, storage_key):
        raise AssertionError(
            "Streaming execution must resolve the dataset before opening storage"
        )


class StreamingTabularReader:

    def stream(self, filename, source):
        raise AssertionError(
            "Streaming execution must resolve the dataset before reading"
        )


def test_streaming_execution_resolves_persisted_dataset():
    engine = WorkflowEngine(
        workflows=StreamingDatasetWorkflow(),
        capability_execution=None,
        executions=StreamingExecutionRepository(),
    )

    try:
        engine.execute(
            workflow_id="wf-stream",
            execution_id="exec-stream",
            inputs={},
            dataset_id="dataset-1",
        )
    except Exception as exc:
        assert "dataset" in str(exc).lower()
    else:
        raise AssertionError(
            "Streaming execution must resolve the persisted dataset"
        )


class ResolvableStreamingDataset:

    def get(self, dataset_id):
        class Dataset:
            storage_key = "dataset-1.csv"
            filename = "dataset-1.csv"

        return Dataset()


class TrackingStreamingStorage:

    def __init__(self):
        self.opened = []

    def open(self, *, storage_key):
        self.opened.append(storage_key)

        class Source:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return Source()


class TrackingStreamingReader:

    def __init__(self):
        self.calls = []

    def stream(self, filename, source):
        self.calls.append((filename, source))
        return iter([])


def test_streaming_execution_opens_persisted_dataset_source():
    storage = TrackingStreamingStorage()
    reader = TrackingStreamingReader()

    engine = WorkflowEngine(
        workflows=StreamingDatasetWorkflow(),
        capability_execution=None,
        executions=StreamingExecutionRepository(),
        datasets=ResolvableStreamingDataset(),
        streaming_reader=reader,
        dataset_storage=storage,
    )

    engine.execute(
        workflow_id="wf-stream",
        execution_id="exec-stream",
        inputs={},
        dataset_id="dataset-1",
    )

    assert storage.opened == ["dataset-1.csv"]
    assert len(reader.calls) == 1
    assert reader.calls[0][0] == "dataset-1.csv"


class ChunkTrackingStreamingReader:

    def __init__(self):
        self.chunks = [
            {"rows": [1, 2]},
            {"rows": [3, 4]},
            {"rows": [5]},
        ]

    def stream(self, filename, source):
        return iter(self.chunks)


class ChunkTrackingCapabilityExecution:

    def __init__(self):
        self.calls = []

    def execute_plan(self, **kwargs):
        self.calls.append(kwargs)

        chunk = kwargs["inputs"]["frame"]

        return CapabilityExecutionResult(
            outputs={
                "processed_rows": len(chunk["rows"]),
            },
            plan=kwargs["plan"],
            trace=ExecutionTrace(
                execution_id=kwargs["execution_id"],
                records=(),
            ),
        )


def test_streaming_execution_processes_each_chunk_without_full_dataset():
    storage = TrackingStreamingStorage()
    reader = ChunkTrackingStreamingReader()
    capability_execution = ChunkTrackingCapabilityExecution()
    executions = StreamingExecutionRepository()

    engine = WorkflowEngine(
        workflows=StreamingDatasetWorkflow(),
        capability_execution=capability_execution,
        executions=executions,
        datasets=ResolvableStreamingDataset(),
        streaming_reader=reader,
        dataset_storage=storage,
    )

    runtime = engine.execute(
        workflow_id="wf-stream",
        execution_id="exec-stream",
        inputs={},
        dataset_id="dataset-1",
    )

    assert runtime.success is True
    assert len(capability_execution.calls) == 3

    assert [
        call["inputs"]["frame"]["rows"]
        for call in capability_execution.calls
    ] == [
        [1, 2],
        [3, 4],
        [5],
    ]


def test_streaming_execution_does_not_accumulate_chunk_outputs():
    storage = TrackingStreamingStorage()
    reader = ChunkTrackingStreamingReader()
    capability_execution = ChunkTrackingCapabilityExecution()

    engine = WorkflowEngine(
        workflows=StreamingDatasetWorkflow(),
        capability_execution=capability_execution,
        executions=StreamingExecutionRepository(),
        datasets=ResolvableStreamingDataset(),
        streaming_reader=reader,
        dataset_storage=storage,
    )

    runtime = engine.execute(
        workflow_id="wf-stream",
        execution_id="exec-stream",
        inputs={},
        dataset_id="dataset-1",
    )

    assert runtime.success is True

    assert runtime.outputs == {
        "processed_chunks": 3,
        "processed_rows": 5,
    }
