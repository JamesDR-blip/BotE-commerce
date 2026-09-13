import pandas as pd
from types import SimpleNamespace

from domain.capabilities import CapabilityContext, CapabilityResult, CapabilitySpec
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from execution.capabilities.capability_execution_service import CapabilityExecutionService
from execution.capabilities.capability_executor import CapabilityExecutor
from execution.shadow_execution_runner import ShadowExecutionRunner


class EchoCapability:
    spec = CapabilitySpec(
        id="echo",
        version="1.0",
        description="Echo frame",
        input_keys=("frame",),
        required_input_keys=("frame",),
        output_keys=("frame",),
        input_types={"frame": pd.DataFrame},
        output_types={"frame": pd.DataFrame},
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        frame = context.inputs["frame"].copy(deep=True)
        frame["processed"] = True
        return CapabilityResult(
            outputs={"frame": frame},
            success=True,
        )


class FailingCapability:
    spec = CapabilitySpec(
        id="failing",
        version="1.0",
        description="Always fails",
        input_keys=(),
        required_input_keys=(),
        output_keys=(),
        input_types={},
        output_types={},
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(
            outputs={},
            success=False,
            error="simulation failure",
        )


def make_runner(*capabilities):
    registry = CapabilityRegistry()

    for capability in capabilities:
        registry.register(capability)

    executor = CapabilityExecutor(registry)
    execution = CapabilityExecutionService(executor=executor)

    return ShadowExecutionRunner(
        capability_execution=execution,
    )


def test_simulation_is_ephemeral_and_does_not_mutate_inputs():
    runner = make_runner(EchoCapability())

    frame = pd.DataFrame(
        {
            "sku": ["A", "B"],
            "price": [10, 20],
        }
    )

    original = frame.copy(deep=True)

    result = runner.simulate(
        workflow_id="wf-1",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="echo",
                ),
            )
        ),
        inputs={"frame": frame},
    )

    assert result.success is True
    assert result.simulation_id
    assert result.workflow_id == "wf-1"
    assert result.workflow_version == "1.0"

    pd.testing.assert_frame_equal(frame, original)

    assert "frame" in result.outputs
    assert "frame" in result.diff.changed_keys

    diff = result.diff.tabular[0]
    assert diff.before_rows == 2
    assert diff.after_rows == 2
    assert "processed" not in diff.before_columns
    assert "processed" in diff.after_columns


def test_simulation_bounds_materialized_row_diffs():
    runner = make_runner(EchoCapability())

    frame = pd.DataFrame({"sku": ["A", "B", "C"]})

    result = runner.simulate(
        workflow_id="wf-1",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="echo",
                ),
            )
        ),
        inputs={"frame": frame},
        max_diff_rows=1,
    )

    diff = result.diff.tabular[0]

    assert len(diff.row_diffs) == 1
    assert diff.truncated is True


def test_simulation_failure_is_returned_without_production_state():
    runner = make_runner(FailingCapability())

    result = runner.simulate(
        workflow_id="wf-1",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="failing",
                ),
            )
        ),
        inputs={},
    )

    assert result.success is False
    assert result.error == "simulation failure"
    assert result.outputs == {}


def test_simulation_rejects_invalid_diff_limit():
    runner = make_runner(EchoCapability())

    try:
        runner.simulate(
            workflow_id="wf-1",
            workflow_version="1.0",
            plan=ExecutionPlan(steps=()),
            inputs={},
            max_diff_rows=-1,
        )
    except ValueError as exc:
        assert str(exc) == "max_diff_rows must be non-negative"
    else:
        raise AssertionError("Expected ValueError")

class FakeDatasetStorage:
    def __init__(self, source):
        self.source = source
        self.opened_with = None
        self.write_called = False

    def open(self, *, storage_key):
        self.opened_with = storage_key
        return self

    def __enter__(self):
        return self.source

    def __exit__(self, exc_type, exc, tb):
        return False

    def save(self, *args, **kwargs):
        self.write_called = True
        raise AssertionError("Simulation must not write dataset storage")

    def save_stream(self, *args, **kwargs):
        self.write_called = True
        raise AssertionError("Simulation must not write dataset storage")


class FakeStreamingReader:
    def __init__(self, chunks):
        self.chunks = chunks
        self.streamed_with = None

    def stream(self, filename, source):
        self.streamed_with = (filename, source)
        yield from self.chunks


def make_streaming_runner(*capabilities, chunks):
    registry = CapabilityRegistry()

    for capability in capabilities:
        registry.register(capability)

    executor = CapabilityExecutor(registry)
    execution = CapabilityExecutionService(executor=executor)

    storage = FakeDatasetStorage(source=object())
    reader = FakeStreamingReader(chunks)

    runner = ShadowExecutionRunner(
        capability_execution=execution,
        dataset_storage=storage,
        streaming_reader=reader,
    )

    return runner, storage, reader


def test_streaming_simulation_reads_dataset_without_writing_storage():
    runner, storage, reader = make_streaming_runner(
        EchoCapability(),
        chunks=[
            pd.DataFrame({"sku": ["A", "B"]}),
            pd.DataFrame({"sku": ["C"]}),
        ],
    )

    dataset = SimpleNamespace(
        storage_key="datasets/input.csv",
        filename="input.csv",
    )

    result = runner.simulate(
        workflow_id="wf-stream",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="echo",
                ),
            ),
            metadata={"execution": {"mode": "streaming"}},
        ),
        inputs={},
        dataset=dataset,
        max_diff_rows=1,
    )

    assert result.success is True
    assert result.outputs == {
        "processed_chunks": 2,
        "processed_rows": 3,
    }

    assert storage.opened_with == "datasets/input.csv"
    assert reader.streamed_with[0] == "input.csv"
    assert storage.write_called is False

    assert result.diff.changed_keys == ("frame",)
    diff = result.diff.tabular[0]
    assert diff.before_rows == 3
    assert diff.after_rows == 3
    assert diff.added_rows == 0
    assert diff.removed_rows == 0
    assert diff.changed_rows == 3
    assert len(diff.row_diffs) == 1
    assert diff.truncated is True


class MutatingAuxiliaryInputCapability:
    spec = CapabilitySpec(
        id="mutate_aux",
        version="1.0",
        description="Mutates an auxiliary input",
        input_keys=("frame", "options"),
        required_input_keys=("frame", "options"),
        output_keys=("frame",),
        input_types={
            "frame": pd.DataFrame,
            "options": dict,
        },
        output_types={"frame": pd.DataFrame},
    )

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        context.inputs["options"]["mutated"] = True
        frame = context.inputs["frame"].copy(deep=True)
        frame["processed"] = True
        return CapabilityResult(
            outputs={"frame": frame},
            success=True,
        )


def test_streaming_simulation_does_not_mutate_auxiliary_inputs():
    runner, _, _ = make_streaming_runner(
        MutatingAuxiliaryInputCapability(),
        chunks=[pd.DataFrame({"sku": ["A"]})],
    )

    dataset = SimpleNamespace(
        storage_key="datasets/input.csv",
        filename="input.csv",
    )

    options = {"mode": "safe"}
    original_options = dict(options)

    result = runner.simulate(
        workflow_id="wf-stream",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="mutate_aux",
                ),
            ),
            metadata={"execution": {"mode": "streaming"}},
        ),
        inputs={"options": options},
        dataset=dataset,
    )

    assert result.success is True
    assert options == original_options

def test_streaming_simulation_requires_dataset():
    runner, _, _ = make_streaming_runner(
        EchoCapability(),
        chunks=[],
    )

    result = runner.simulate(
        workflow_id="wf-stream",
        workflow_version="1.0",
        plan=ExecutionPlan(
            steps=(
                PlanStep(
                    capability_id="echo",
                ),
            ),
            metadata={"execution": {"mode": "streaming"}},
        ),
        inputs={},
    )

    assert result.success is False
    assert result.error == "Streaming workflow simulation requires a dataset"



