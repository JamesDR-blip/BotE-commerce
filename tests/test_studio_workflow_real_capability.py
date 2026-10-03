from domain.plans import ExecutionPlan, PlanStep
from domain.identity import CurrentUser
from configs.settings import Settings
from services.container import build_container
import pandas as pd
from application.workspace.project_service import WorkspaceProjectService
from contextlib import nullcontext

def test_studio_workflow_executes_real_capability():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    authoring_service = container.workflow_authoring
    workspace_projects = container.workspace_projects
    current_user = CurrentUser(
        user_id="test-user"
    )

    workspace_projects.create_workspace(
        current_user=current_user,
        workspace_id="ws-1",
        name="Demo",
    )

    workspace_projects.create_project(
        current_user=current_user,
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.normalize",
                capability_version="1.0",
                parameters={},
            ),
        ),
        version="1.0",
        metadata={},
    )

    workflow = authoring_service.save_workflow(
        current_user=current_user,
        workflow_id="wf-1",
        project_id="p-1",
        name="Normalize Catalog",
        version="1.0",
        plan=plan,
    )

    assert workflow.id == "wf-1"

    runtime = container.workflow_engine.execute(
        workflow_id="wf-1",
        execution_id="exec-1",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90 Black",
                        "Adidas Ultraboost White",
                    ]
                }
            ),
        }
    )

    assert runtime.success is True

    assert runtime.workflow_id == "wf-1"
    assert runtime.workflow_version == "1.0"

    assert runtime.outputs is not None


def test_studio_workflow_executes_real_capability_chain():
    container = build_container(
        Settings(
            database_url="sqlite://",
        )
    )

    authoring_service = container.workflow_authoring
    workspace_projects = container.workspace_projects

    current_user = CurrentUser(
        user_id="test-user"
    )

    workspace_projects.create_workspace(
        current_user=current_user,
        workspace_id="ws-chain",
        name="Demo Chain",
    )

    workspace_projects.create_project(
        current_user=current_user,
        project_id="p-chain",
        workspace_id="ws-chain",
        name="Catalog Chain",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
                parameters={},
            ),
            PlanStep(
                capability_id="data.validate",
                capability_version="1.0",
                parameters={},
                input_mapping={
                    "frame": "frame",
                    "category": "category",
                },
            ),
        ),
        version="1.0",
        metadata={},
    )

    workflow = authoring_service.save_workflow(
        current_user=current_user,
        workflow_id="wf-chain",
        project_id="p-chain",
        name="Clean and Validate Catalog",
        version="1.0",
        plan=plan,
    )

    assert workflow.id == "wf-chain"

    runtime = container.workflow_engine.execute(
        workflow_id="wf-chain",
        execution_id="exec-chain",
        inputs={
            "frame": pd.DataFrame(
                {
                    "product_title": [
                        "Nike Air Max 90",
                        "Adidas Ultraboost",
                    ],
                }
            ),
        },
    )

    assert runtime.success is True

    assert runtime.workflow_id == "wf-chain"
    assert runtime.workflow_version == "1.0"

    assert "frame" in runtime.outputs
    assert "category" in runtime.outputs
    assert "issues" in runtime.outputs
    assert "rule_version" in runtime.outputs

    assert isinstance(
        runtime.outputs["frame"],
        pd.DataFrame,
    )

    assert isinstance(
        runtime.outputs["category"],
        str,
    )

    assert isinstance(
        runtime.outputs["issues"],
        list,
    )

    assert isinstance(
        runtime.outputs["rule_version"],
        str,
    )
    _assert_streaming_validation_has_same_sync_and_worker_semantics()


def _assert_streaming_validation_has_same_sync_and_worker_semantics():
    container = build_container(Settings(database_url="sqlite://"))
    current_user = CurrentUser(user_id="parity-user")
    container.workspace_projects.create_workspace(
        current_user=current_user,
        workspace_id="ws-parity",
        name="Parity",
    )
    container.workspace_projects.create_project(
        current_user=current_user,
        project_id="project-parity",
        workspace_id="ws-parity",
        name="Parity catalog",
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
                parameters={},
            ),
            PlanStep(
                capability_id="data.validate",
                capability_version="1.0",
                parameters={},
                input_mapping={
                    "frame": "frame",
                    "category": "category",
                },
            ),
        ),
        version="1.0",
        metadata={"execution": {"mode": "streaming", "chunk_size": 2}},
    )
    container.workflow_authoring.save_workflow(
        current_user=current_user,
        workflow_id="wf-parity",
        project_id="project-parity",
        name="Validate catalog",
        version="1.0",
        plan=plan,
    )

    class Dataset:
        filename = "parity.csv"
        storage_key = "parity.csv"

    class DatasetRepository:
        def get(self, dataset_id):
            assert dataset_id == "dataset-parity"
            return Dataset()

    class DatasetStorage:
        def open(self, *, storage_key):
            assert storage_key == "parity.csv"
            return nullcontext(object())

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max 90 Black", "Adidas Ultraboost White"],
            "brand": ["Nike", "Adidas"],
            "price": [120.0, 140.0],
        }
    )

    class Reader:
        def stream(self, filename, source):
            assert filename == "parity.csv"
            return iter([frame.copy()])

    container.workflow_engine.datasets = DatasetRepository()
    container.workflow_engine.dataset_storage = DatasetStorage()
    container.workflow_engine.streaming_reader = Reader()

    sync = container.workflow_engine.execute(
        workflow_id="wf-parity",
        execution_id="exec-sync-parity",
        inputs={"requested_category": "Fashion"},
        dataset_id="dataset-parity",
    )

    container.workflow_engine.create_queued(
        workflow_id="wf-parity",
        execution_id="exec-worker-parity",
        inputs={"requested_category": "Fashion"},
        dataset_id="dataset-parity",
    )
    container.workflow_worker.run("exec-worker-parity")

    worker_record = container.workflow_executions.get("exec-worker-parity")
    sync_record = container.workflow_executions.get("exec-sync-parity")
    assert worker_record is not None
    assert sync_record is not None
    assert sync.success is True
    assert sync_record.status == worker_record.status == "COMPLETED"
    assert sync_record.outputs_json == worker_record.outputs_json
    assert container.executions.get("exec-sync-parity") is None
    assert container.executions.get("exec-worker-parity") is None

    sync_trace = container.workflow_capability_traces.list_by_execution(
        "exec-sync-parity"
    )
    worker_trace = container.workflow_capability_traces.list_by_execution(
        "exec-worker-parity"
    )
    assert [item.capability_id for item in sync_trace] == [
        item.capability_id for item in worker_trace
    ] == ["data.clean", "data.validate"]
    assert [item.status for item in sync_trace] == [
        item.status for item in worker_trace
    ] == ["COMPLETED", "COMPLETED"]
    assert [item.inputs_json for item in sync_trace] == [
        item.inputs_json for item in worker_trace
    ]
    assert [item.outputs_json for item in sync_trace] == [
        item.outputs_json for item in worker_trace
    ]

    sync_error = container.workflow_engine.execute(
        workflow_id="wf-parity",
        execution_id="exec-sync-error-parity",
        inputs={"requested_category": "NotARealCategory"},
        dataset_id="dataset-parity",
    )
    container.workflow_engine.create_queued(
        workflow_id="wf-parity",
        execution_id="exec-worker-error-parity",
        inputs={"requested_category": "NotARealCategory"},
        dataset_id="dataset-parity",
    )
    container.workflow_worker.run("exec-worker-error-parity")

    sync_error_record = container.workflow_executions.get(
        "exec-sync-error-parity"
    )
    worker_error_record = container.workflow_executions.get(
        "exec-worker-error-parity"
    )
    assert sync_error.success is False
    assert sync_error_record is not None
    assert worker_error_record is not None
    assert sync_error_record.status == worker_error_record.status == "FAILED"
    assert sync_error_record.error == worker_error_record.error
    assert sync_error_record.error == "Unsupported category: NotARealCategory"
    sync_error_trace = container.workflow_capability_traces.list_by_execution(
        "exec-sync-error-parity"
    )
    worker_error_trace = container.workflow_capability_traces.list_by_execution(
        "exec-worker-error-parity"
    )
    assert [item.capability_id for item in sync_error_trace] == [
        item.capability_id for item in worker_error_trace
    ]
    assert [item.status for item in sync_error_trace] == [
        item.status for item in worker_error_trace
    ]
    assert [item.error for item in sync_error_trace] == [
        item.error for item in worker_error_trace
    ]
