import pytest
from io import BytesIO

from database.models import Base

from domain.identity import CurrentUser
from domain.plans import ExecutionPlan

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository

from application.datasets.dataset_service import DatasetService
from application.workflows.authoring_service import WorkflowAuthoringService
from application.workspace.project_service import WorkspaceProjectService


def build_services():
    engine = create_engine(
        "sqlite://"
    )

    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    workspaces = WorkspaceRepository(
        sessions
    )
    projects = ProjectRepository(
        sessions
    )
    datasets = DatasetRepository(
        sessions
    )
    workflows = WorkflowRepository(
        sessions
    )

    workflow_authoring = WorkflowAuthoringService(
        workflows=workflows,
        projects=projects,
    )

    workspace_projects = WorkspaceProjectService(
        workspaces=workspaces,
        projects=projects,
    )

    dataset_service = DatasetService(
        datasets=datasets,
        projects=projects,
    )

    return (
        workflow_authoring,
        workspace_projects,
        dataset_service,
    )

def test_create_workspace_project_dataset():

    service, workspace_projects, dataset_service = build_services()

    current_user = CurrentUser(
        user_id="test-user"
    )

    workspace_projects.create_workspace(
        current_user=current_user,
        workspace_id="ws-1",
        name="Demo",
    )

    project = workspace_projects.create_project(
        current_user=current_user,
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )

    dataset = dataset_service.create_dataset(
        current_user=current_user,
        dataset_id="d-1",
        project_id=project.id,
        name="catalog.csv",
        source_type="upload",
        metadata={
            "rows": 1000
        },
    )

    assert dataset.name == "catalog.csv"



def test_save_workflow():

    authoring_service, workspace_projects, _ = build_services()

    user = CurrentUser(user_id="test-user")

    workspace_projects.create_workspace(
        current_user=user,
        workspace_id="ws-1",
        name="Test Workspace",
    )

    workspace_projects.create_project(
        current_user=user,
        project_id="p-1",
        workspace_id="ws-1",
        name="Test Project",
    )

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )


    workflow = authoring_service.save_workflow(
        current_user=user,
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1",
        plan=plan,
    )


    assert workflow.active_version == "1"

def test_dataset_cannot_be_created_for_other_users_project():
    service, workspace_projects, dataset_service = build_services()

    owner = CurrentUser(user_id="owner")
    other_user = CurrentUser(user_id="other")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-owner",
        name="Owner Workspace",
    )

    project = workspace_projects.create_project(
        current_user=owner,
        project_id="p-owner",
        workspace_id="ws-owner",
        name="Owner Project",
    )

    with pytest.raises(ValueError, match="Project not found"):
        dataset_service.create_dataset(
            current_user=other_user,
            dataset_id="d-forbidden",
            project_id=project.id,
            name="forbidden.csv",
            source_type="upload",
            metadata={},
        )

def test_workflow_cannot_be_created_for_other_users_project():
    authoring_service, workspace_projects, _ = build_services()

    owner = CurrentUser(user_id="owner")
    other_user = CurrentUser(user_id="other")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-owner",
        name="Owner Workspace",
    )

    project = workspace_projects.create_project(
        current_user=owner,
        project_id="p-owner",
        workspace_id="ws-owner",
        name="Owner Project",
    )

    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )

    with pytest.raises(
        ValueError,
        match="Project not found",
    ):
        authoring_service.save_workflow(
            current_user=other_user,
            workflow_id="wf-forbidden",
            project_id=project.id,
            name="Forbidden Workflow",
            version="1",
            plan=plan,
        )

def test_ingest_dataset_stream_delegates_after_project_ownership_check():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            assert project_id == "p-1"
            assert owner_id == "user-1"
            return object()

    class FakeIngestion:
        def __init__(self):
            self.kwargs = None

        def ingest_streaming(self, **kwargs):
            self.kwargs = kwargs
            return {"status": "READY"}

    ingestion = FakeIngestion()

    dataset_service = DatasetService(
        datasets=None,
        projects=FakeProjects(),
        ingestion=ingestion,
    )

    source = BytesIO(b"id,value\n1,100\n")

    result = dataset_service.ingest_dataset_stream(
        dataset_id="d-1",
        project_id="p-1",
        name="catalog",
        current_user=CurrentUser(user_id="user-1"),
        filename="catalog.csv",
        source=source,
    )

    assert result == {"status": "READY"}
    assert ingestion.kwargs["dataset_id"] == "d-1"
    assert ingestion.kwargs["project_id"] == "p-1"
    assert ingestion.kwargs["name"] == "catalog"
    assert ingestion.kwargs["filename"] == "catalog.csv"
    assert ingestion.kwargs["source"] is source

def test_ingest_dataset_stream_rejects_other_users_project():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            return None

    class FakeIngestion:
        def ingest_streaming(self, **kwargs):
            raise AssertionError("ingestion must not be called")

    dataset_service = DatasetService(
        datasets=None,
        projects=FakeProjects(),
        ingestion=FakeIngestion(),
    )

    with pytest.raises(ValueError, match="Project not found"):
        dataset_service.ingest_dataset_stream(
            dataset_id="d-1",
            project_id="p-1",
            name="catalog",
            current_user=CurrentUser(user_id="other-user"),
            filename="catalog.csv",
            source=BytesIO(b"id,value\n1,100\n"),
        )