from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.identity import CurrentUser
from database.models import Base

from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository

from services.studio_service import StudioService

from domain.plans import ExecutionPlan



def build_service():

    engine = create_engine(
        "sqlite://"
    )

    Base.metadata.create_all(engine)

    sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return StudioService(
        workspaces=WorkspaceRepository(
            sessions
        ),
        projects=ProjectRepository(
            sessions
        ),
        datasets=DatasetRepository(
            sessions
        ),
        workflows=WorkflowRepository(
            sessions
        ),
    )



def test_create_workspace_project_dataset():

    service = build_service()

    current_user = CurrentUser(
            user_id="test-user"
        )

    service.create_workspace(
        current_user=current_user,
        workspace_id="ws-1",
        name="Demo",
    )


    project = service.create_project(
        current_user=current_user,
        project_id="p-1",
        workspace_id="ws-1",
        name="Catalog",
    )


    dataset = service.create_dataset(
        dataset_id="d-1",
        project_id=project.id,
        name="catalog.csv",
        source_type="upload",
        metadata={
            "rows":1000
        },
    )


    assert dataset.name == "catalog.csv"



def test_save_workflow():

    service = build_service()


    plan = ExecutionPlan(
        steps=(),
        version="1.0",
        metadata={},
    )


    workflow = service.save_workflow(
        workflow_id="wf-1",
        project_id="p-1",
        name="Validation",
        version="1",
        plan=plan,
    )


    assert workflow.active_version == "1"

def test_create_project_requires_owned_workspace():

    service = build_service()

    owner = CurrentUser(
        user_id="owner-1"
    )

    other_user = CurrentUser(
        user_id="owner-2"
    )

    service.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Owner Workspace",
    )

    try:
        service.create_project(
            current_user=other_user,
            project_id="p-1",
            workspace_id="ws-1",
            name="Forbidden Project",
        )
    except ValueError as exc:
        assert str(exc) == "Workspace not found: ws-1"
    else:
        raise AssertionError(
            "Expected project creation to be rejected"
        )

def test_get_project_requires_owned_workspace():

    service = build_service()

    owner = CurrentUser(user_id="owner-1")
    other_user = CurrentUser(user_id="owner-2")

    service.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Owner Workspace",
    )

    service.create_project(
        current_user=owner,
        project_id="p-1",
        workspace_id="ws-1",
        name="Owner Project",
    )

    assert service.get_project(
        current_user=owner,
        project_id="p-1",
    ) is not None

    assert service.get_project(
        current_user=other_user,
        project_id="p-1",
    ) is None

def test_list_projects_requires_owned_workspace():

    service = build_service()

    owner = CurrentUser(user_id="owner-1")
    other_user = CurrentUser(user_id="owner-2")

    service.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Owner Workspace",
    )

    service.create_project(
        current_user=owner,
        project_id="p-1",
        workspace_id="ws-1",
        name="Owner Project",
    )

    assert [
        project.id
        for project in service.list_projects(
            current_user=owner,
            workspace_id="ws-1",
        )
    ] == ["p-1"]

    try:
        service.list_projects(
            current_user=other_user,
            workspace_id="ws-1",
        )
    except ValueError as exc:
        assert str(exc) == "Workspace not found: ws-1"
    else:
        raise AssertionError(
            "Expected project listing to be rejected"
        )