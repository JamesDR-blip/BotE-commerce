from domain.identity import CurrentUser
from repositories.projects import ProjectRepository
from repositories.workspaces import WorkspaceRepository
from application.workspace.project_service import WorkspaceProjectService

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base


def create_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

def build_workspace_project_service(service):
    return WorkspaceProjectService(
        workspaces=service.workspaces,
        projects=service.projects,
    )

def build_service():
    return WorkspaceProjectService(
        workspaces=WorkspaceRepository(create_session()),
        projects=ProjectRepository(create_session()),
    )


def test_create_workspace_assigns_current_user_as_owner():
    service = build_service()
    workspace_projects = build_workspace_project_service(service)
    user = CurrentUser(user_id="user-1")

    workspace = workspace_projects.create_workspace(
        current_user=user,
        workspace_id="ws-1",
        name="Workspace 1",
    )

    assert workspace.id == "ws-1"
    assert workspace.owner_id == "user-1"


def test_workspace_access_is_scoped_to_owner():
    service = build_service()
    workspace_projects = build_workspace_project_service(service)

    owner = CurrentUser(user_id="user-1")
    other_user = CurrentUser(user_id="user-2")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Workspace 1",
    )

    assert service.get_workspace(
        current_user=owner,
        workspace_id="ws-1",
    ) is not None

    assert service.get_workspace(
        current_user=other_user,
        workspace_id="ws-1",
    ) is None


def test_create_project_requires_owned_workspace():
    service = build_service()
    workspace_projects = build_workspace_project_service(service)

    owner = CurrentUser(user_id="user-1")
    other_user = CurrentUser(user_id="user-2")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Workspace 1",
    )

    try:
        workspace_projects.create_project(
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
    workspace_projects = build_workspace_project_service(service)

    owner = CurrentUser(user_id="user-1")
    other_user = CurrentUser(user_id="user-2")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Workspace 1",
    )

    workspace_projects.create_project(
        current_user=owner,
        project_id="p-1",
        workspace_id="ws-1",
        name="Project 1",
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
    workspace_projects = build_workspace_project_service(service)

    owner = CurrentUser(user_id="user-1")
    other_user = CurrentUser(user_id="user-2")

    workspace_projects.create_workspace(
        current_user=owner,
        workspace_id="ws-1",
        name="Workspace 1",
    )

    workspace_projects.create_project(
        current_user=owner,
        project_id="p-1",
        workspace_id="ws-1",
        name="Project 1",
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
