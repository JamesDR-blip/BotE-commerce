from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from io import BytesIO

import pandas as pd
import pytest

from application.changesets.changeset_service import ChangeSetService
from domain.changeset import ChangeSetStatus
from domain.plans import ExecutionPlan


@dataclass
class FakeExecution:
    id: str
    workflow_id: str
    workflow_version: str
    dataset_id: str | None
    status: str
    inputs_json: str | None = None


@dataclass
class FakeDataset:
    id: str
    project_id: str
    name: str
    source_type: str
    metadata: dict
    filename: str
    file_format: str
    storage_key: str
    content_hash: str | None = None


@dataclass
class FakeWorkflowVersion:
    workflow_id: str
    version: str
    plan_json: dict


class FakeExecutionRepository:
    def __init__(self, execution):
        self.execution = execution

    def get(self, execution_id):
        if execution_id != self.execution.id:
            return None
        return self.execution


class FakeDatasetRepository:
    def __init__(self, dataset):
        self.dataset = dataset

    def get(self, dataset_id):
        if dataset_id != self.dataset.id:
            return None
        return self.dataset


class FakeWorkflowRepository:
    def __init__(self, version):
        self.version = version
        self.requested = None

    def get_version(self, workflow_id, version):
        self.requested = (workflow_id, version)

        if (
            workflow_id != self.version.workflow_id
            or version != self.version.version
        ):
            return None

        return self.version


class FakeStorage:
    def __init__(self, artifacts):
        self.artifacts = dict(artifacts)

    def open(self, *, storage_key):
        if storage_key not in self.artifacts:
            raise FileNotFoundError(storage_key)

        return BytesIO(self.artifacts[storage_key])

    def save(self, *, storage_key, content):
        self.artifacts[storage_key] = content
        return storage_key

    def save_stream(self, *, storage_key, source):
        content = source.read()
        self.artifacts[storage_key] = content
        return storage_key


class FakeMaterializer:
    def __init__(self, storage):
        self.storage = storage
        self.calls = []

    def materialize(
        self,
        *,
        frame,
        file_format,
        changeset_id,
    ):
        content = frame.to_csv(
            index=False,
            lineterminator="\n",
        ).encode("utf-8")

        storage_key = (
            f"changesets/{changeset_id}/after.{file_format}"
        )

        self.storage.save(
            storage_key=storage_key,
            content=content,
        )

        content_hash = hashlib.sha256(content).hexdigest()

        self.calls.append(
            {
                "frame": frame.copy(deep=True),
                "file_format": file_format,
                "changeset_id": changeset_id,
            }
        )

        return storage_key, content_hash


class FakeCapabilityExecution:
    def __init__(self, after_frame):
        self.after_frame = after_frame
        self.calls = []

    def execute_plan(
        self,
        *,
        plan,
        inputs,
        execution_id,
    ):
        self.calls.append(
            {
                "plan": plan,
                "inputs": inputs,
                "execution_id": execution_id,
            }
        )

        return type(
            "Result",
            (),
            {
                "outputs": {
                    "frame": self.after_frame.copy(deep=True),
                }
            },
        )()


class FakeChangeSetRepository:
    def __init__(self):
        self.created = []

    def create(self, changeset, items):
        self.created.append(
            {
                "changeset": changeset,
                "items": list(items),
            }
        )
        return changeset


def make_service(
    *,
    before_frame,
    after_frame,
    execution_status="COMPLETED",
    plan_json=None,
    content_hash=None,
):
    before_bytes = before_frame.to_csv(
        index=False,
        lineterminator="\n",
    ).encode("utf-8")

    before_storage_key = "datasets/dataset-1.csv"

    storage = FakeStorage(
        {
            before_storage_key: before_bytes,
        }
    )

    dataset = FakeDataset(
        id="dataset-1",
        project_id="project-1",
        name="input",
        source_type="upload",
        metadata={},
        filename="input.csv",
        file_format="csv",
        storage_key=before_storage_key,
        content_hash=content_hash,
    )

    execution = FakeExecution(
        id="execution-1",
        workflow_id="workflow-1",
        workflow_version="2.0",
        dataset_id="dataset-1",
        status=execution_status,
        inputs_json=json.dumps(
            {
                "requested_category": "product",
            }
        ),
    )

    if plan_json is None:
        plan_json = {
            "version": "1.0",
            "steps": [],
            "metadata": {},
        }

    version = FakeWorkflowVersion(
        workflow_id="workflow-1",
        version="2.0",
        plan_json=plan_json,
    )

    executions = FakeExecutionRepository(execution)
    datasets = FakeDatasetRepository(dataset)
    workflows = FakeWorkflowRepository(version)
    capability_execution = FakeCapabilityExecution(after_frame)
    materializer = FakeMaterializer(storage)
    changesets = FakeChangeSetRepository()

    service = ChangeSetService(
        workflows=workflows,
        executions=executions,
        datasets=datasets,
        dataset_storage=storage,
        capability_execution=capability_execution,
        artifact_materializer=materializer,
        changesets=changesets,
    )

    return (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    )


def test_prepare_creates_prepared_changeset_and_items():
    before = pd.DataFrame(
        {
            "sku": ["A", "B"],
            "price": [10, 20],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A", "B"],
            "price": [15, 20],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
    )

    changeset = service.prepare(
        execution_id=execution.id,
    )

    assert changeset.status == ChangeSetStatus.PREPARED
    assert changeset.dataset_id == dataset.id
    assert changeset.execution_id == execution.id
    assert changeset.workflow_id == "workflow-1"
    assert changeset.workflow_version == "2.0"

    assert changeset.before_storage_key == dataset.storage_key
    assert changeset.after_storage_key.startswith(
        "changesets/"
    )

    assert changeset.after_content_hash == hashlib.sha256(
        storage.artifacts[changeset.after_storage_key]
    ).hexdigest()

    assert len(changesets.created) == 1

    items = changesets.created[0]["items"]

    assert len(items) == 1
    assert items[0].entity == "dataset_row"
    assert items[0].record_id == "0"
    assert items[0].before_snapshot == {
        "sku": "A",
        "price": 10,
    }
    assert items[0].after_snapshot == {
        "sku": "A",
        "price": 15,
    }


def test_prepare_injects_before_frame_without_mutating_original():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
    )

    service.prepare(
        execution_id=execution.id,
    )

    call = capability_execution.calls[0]

    assert call["execution_id"] == execution.id
    assert isinstance(call["plan"], ExecutionPlan)

    execution_frame = call["inputs"]["frame"]

    pd.testing.assert_frame_equal(
        execution_frame,
        before,
    )

    assert execution_frame is not before


def test_prepare_uses_persisted_execution_workflow_version():
    before = pd.DataFrame({"sku": ["A"]})
    after = pd.DataFrame({"sku": ["B"]})

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
    )

    service.prepare(
        execution_id=execution.id,
    )

    assert workflows.requested == (
        "workflow-1",
        "2.0",
    )


def test_prepare_ignores_unchanged_rows():
    before = pd.DataFrame(
        {
            "sku": ["A", "B", "C"],
            "price": [10, 20, 30],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A", "B", "C"],
            "price": [10, 25, 30],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
    )

    service.prepare(
        execution_id=execution.id,
    )

    items = changesets.created[0]["items"]

    assert [item.record_id for item in items] == ["1"]


def test_prepare_creates_items_for_added_and_removed_rows():
    before = pd.DataFrame(
        {
            "sku": ["A", "B"],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A", "B", "C"],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
    )

    service.prepare(
        execution_id=execution.id,
    )

    items = changesets.created[0]["items"]

    assert len(items) == 1
    assert items[0].record_id == "2"
    assert items[0].before_snapshot == {}
    assert items[0].after_snapshot == {"sku": "C"}


def test_prepare_rejects_non_completed_execution():
    before = pd.DataFrame({"sku": ["A"]})
    after = pd.DataFrame({"sku": ["B"]})

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status="RUNNING",
    )

    with pytest.raises(
        ValueError,
        match="Only COMPLETED workflow executions",
    ):
        service.prepare(
            execution_id=execution.id,
        )

    assert capability_execution.calls == []
    assert changesets.created == []
    assert materializer.calls == []


def test_prepare_rejects_streaming_plan_without_persisting_changeset():
    before = pd.DataFrame({"sku": ["A"]})
    after = pd.DataFrame({"sku": ["B"]})

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        plan_json={
            "version": "1.0",
            "steps": [],
            "metadata": {
                "execution": {
                    "mode": "streaming",
                },
            },
        },
    )

    with pytest.raises(
        NotImplementedError,
        match="Streaming ChangeSet materialization",
    ):
        service.prepare(
            execution_id=execution.id,
        )

    assert capability_execution.calls == []
    assert materializer.calls == []
    assert changesets.created == []


def test_prepare_hashes_before_artifact_when_dataset_hash_missing():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        content_hash=None,
    )

    expected_hash = hashlib.sha256(
        storage.artifacts[dataset.storage_key]
    ).hexdigest()

    changeset = service.prepare(
        execution_id=execution.id,
    )

    assert changeset.before_content_hash == expected_hash

def test_prepare_candidate_allows_queued_execution():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status="QUEUED",
    )

    changeset = service.prepare_candidate(
        execution_id=execution.id,
    )

    assert changeset.status == ChangeSetStatus.PREPARED
    assert changeset.execution_id == execution.id
    assert changeset.dataset_id == dataset.id

    assert len(changesets.created) == 1
    assert len(changesets.created[0]["items"]) == 1


def test_prepare_candidate_allows_pending_approval_execution():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status="PENDING_APPROVAL",
    )

    changeset = service.prepare_candidate(
        execution_id=execution.id,
    )

    assert changeset.status == ChangeSetStatus.PREPARED
    assert len(changesets.created) == 1


def test_prepare_candidate_allows_running_execution():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status="RUNNING",
    )

    changeset = service.prepare_candidate(
        execution_id=execution.id,
    )

    assert changeset.status == ChangeSetStatus.PREPARED
    assert len(changesets.created) == 1


@pytest.mark.parametrize(
    "status",
    [
        "FAILED",
        "CANCELLED",
    ],
)
def test_prepare_candidate_rejects_terminal_execution(status):
    before = pd.DataFrame({"sku": ["A"], "price": [10]})
    after = pd.DataFrame({"sku": ["A"], "price": [15]})

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status=status,
    )

    with pytest.raises(ValueError, match="non-terminal"):
        service.prepare_candidate(
            execution_id=execution.id,
        )

    assert changesets.created == []
    assert materializer.calls == []
    assert capability_execution.calls == []


def test_prepare_candidate_does_not_mutate_dataset_pointer():
    before = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [10],
        }
    )

    after = pd.DataFrame(
        {
            "sku": ["A"],
            "price": [15],
        }
    )

    (
        service,
        execution,
        dataset,
        workflows,
        capability_execution,
        materializer,
        changesets,
        storage,
    ) = make_service(
        before_frame=before,
        after_frame=after,
        execution_status="PENDING_APPROVAL",
    )

    original_storage_key = dataset.storage_key
    original_content_hash = dataset.content_hash

    changeset = service.prepare_candidate(
        execution_id=execution.id,
    )

    assert dataset.storage_key == original_storage_key
    assert dataset.content_hash == original_content_hash

    assert changeset.before_storage_key == original_storage_key
    assert changeset.after_storage_key != original_storage_key

    assert changesets.created[0]["changeset"].status == (
        ChangeSetStatus.PREPARED
    )
