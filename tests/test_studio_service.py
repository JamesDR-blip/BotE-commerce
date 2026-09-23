import pytest
from io import BytesIO
from types import SimpleNamespace

from database.models import Base

from domain.exceptions import QuotaExceededError
from domain.quota import QuotaDimension
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

class FakeAuthorization:
    def authorize(self, **kwargs):
        return None


class FakeQuotaService:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def check(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error


def test_create_dataset_checks_dataset_quota():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            assert project_id == "p-1"
            assert owner_id == "user-1"
            return SimpleNamespace(id="p-1", workspace_id="ws-1")

    class FakeWorkspaces:
        def get_for_owner(self, *, workspace_id, owner_id):
            assert workspace_id == "ws-1"
            assert owner_id == "user-1"
            return SimpleNamespace(organization_id="org-1")

    class FakeDatasets:
        def __init__(self):
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(id="d-1", **kwargs)

    quota = FakeQuotaService()
    datasets = FakeDatasets()

    dataset_service = DatasetService(
        datasets=datasets,
        projects=FakeProjects(),
        workspaces=FakeWorkspaces(),
        authorization=FakeAuthorization(),
        quota_service=quota,
    )

    result = dataset_service.create_dataset(
        current_user=CurrentUser(user_id="user-1"),
        dataset_id="d-1",
        project_id="p-1",
        name="catalog.csv",
        source_type="upload",
        metadata={},
    )

    assert result.id == "d-1"
    assert datasets.kwargs is not None
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.DATASET_COUNT,
            "requested_usage": 1,
        }
    ]


def test_create_dataset_stops_before_mutation_when_quota_exceeded():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            return SimpleNamespace(id="p-1", workspace_id="ws-1")

    class FakeWorkspaces:
        def get_for_owner(self, *, workspace_id, owner_id):
            return SimpleNamespace(organization_id="org-1")

    class FakeDatasets:
        def __init__(self):
            self.called = False

        def create(self, **kwargs):
            self.called = True
            raise AssertionError("dataset mutation must not occur")

    quota = FakeQuotaService(
        error=QuotaExceededError(
            dimension=QuotaDimension.DATASET_COUNT.value,
            current_usage=1,
            requested_usage=1,
            limit=1,
        )
    )
    datasets = FakeDatasets()

    dataset_service = DatasetService(
        datasets=datasets,
        projects=FakeProjects(),
        workspaces=FakeWorkspaces(),
        authorization=FakeAuthorization(),
        quota_service=quota,
    )

    with pytest.raises(QuotaExceededError):
        dataset_service.create_dataset(
            current_user=CurrentUser(user_id="user-1"),
            dataset_id="d-1",
            project_id="p-1",
            name="catalog.csv",
            source_type="upload",
            metadata={},
        )

    assert datasets.called is False
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.DATASET_COUNT,
            "requested_usage": 1,
        }
    ]


def test_ingest_dataset_checks_dataset_and_storage_quotas():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            return SimpleNamespace(id="p-1", workspace_id="ws-1")

    class FakeWorkspaces:
        def get_for_owner(self, *, workspace_id, owner_id):
            return SimpleNamespace(organization_id="org-1")

    class FakeIngestion:
        def __init__(self):
            self.kwargs = None

        def ingest(self, **kwargs):
            self.kwargs = kwargs
            return {"status": "READY"}

    quota = FakeQuotaService()
    ingestion = FakeIngestion()
    content = b"id,value\n1,100\n"

    dataset_service = DatasetService(
        datasets=None,
        projects=FakeProjects(),
        workspaces=FakeWorkspaces(),
        ingestion=ingestion,
        authorization=FakeAuthorization(),
        quota_service=quota,
    )

    result = dataset_service.ingest_dataset(
        dataset_id="d-1",
        project_id="p-1",
        name="catalog",
        current_user=CurrentUser(user_id="user-1"),
        filename="catalog.csv",
        content=content,
    )

    assert result == {"status": "READY"}
    assert ingestion.kwargs is not None
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.DATASET_COUNT,
            "requested_usage": 1,
        },
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.STORAGE_BYTES,
            "requested_usage": len(content),
        },
    ]


def test_ingest_dataset_stream_checks_exact_storage_size():
    class FakeProjects:
        def get_for_owner(self, *, project_id, owner_id):
            return SimpleNamespace(id="p-1", workspace_id="ws-1")

    class FakeWorkspaces:
        def get_for_owner(self, *, workspace_id, owner_id):
            return SimpleNamespace(organization_id="org-1")

    class FakeIngestion:
        def __init__(self):
            self.kwargs = None

        def ingest_streaming(self, **kwargs):
            self.kwargs = kwargs
            return {"status": "READY"}

    quota = FakeQuotaService()
    ingestion = FakeIngestion()
    source = BytesIO(b"id,value\n1,100\n2,200\n")

    dataset_service = DatasetService(
        datasets=None,
        projects=FakeProjects(),
        workspaces=FakeWorkspaces(),
        ingestion=ingestion,
        authorization=FakeAuthorization(),
        quota_service=quota,
    )

    result = dataset_service.ingest_dataset_stream(
        dataset_id="d-1",
        project_id="p-1",
        name="catalog",
        current_user=CurrentUser(user_id="user-1"),
        filename="catalog.csv",
        source=source,
    )

    assert result == {"status": "READY"}
    assert ingestion.kwargs["source"] is source
    assert quota.calls == [
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.DATASET_COUNT,
            "requested_usage": 1,
        },
        {
            "organization_id": "org-1",
            "dimension": QuotaDimension.STORAGE_BYTES,
            "requested_usage": len(b"id,value\n1,100\n2,200\n"),
        },
    ]
