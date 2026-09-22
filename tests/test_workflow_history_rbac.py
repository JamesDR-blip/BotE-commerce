from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.workflows.history_service import WorkflowHistoryService
from database.models import Base
from domain.identity import CurrentUser
from repositories.rbac import RBACRepository
from services.authorization import AuthorizationService


class FakeExecutions:
    def get(self, execution_id):
        if execution_id != "execution-1":
            return None

        return SimpleNamespace(
            id="execution-1",
            workflow_id="workflow-1",
            workflow_version="1.0",
            status="COMPLETED",
            inputs_json="{}",
            outputs_json="{}",
            error=None,
            created_at=None,
            started_at=None,
            finished_at=None,
        )


class FakeTraces:
    def list_by_execution(self, execution_id):
        return []


class FakeWorkflows:
    def __init__(self, owner_id="user-1"):
        self.owner_id = owner_id

    def get_for_owner(self, *, workflow_id, owner_id):
        if workflow_id != "workflow-1" or owner_id != self.owner_id:
            return None

        return SimpleNamespace(
            project_id="project-1",
        )


class FakeProjects:
    def get_for_owner(self, *, project_id, owner_id):
        if project_id != "project-1" or owner_id != "user-1":
            return None

        return SimpleNamespace(
            workspace_id="workspace-1",
        )


class FakeWorkspaces:
    def __init__(self, organization_id="org-1"):
        self.organization_id = organization_id

    def get_for_owner(self, *, workspace_id, owner_id):
        if workspace_id != "workspace-1" or owner_id != "user-1":
            return None

        return SimpleNamespace(
            organization_id=self.organization_id,
        )


def make_service(*, organization_id="org-1"):
    db_engine = create_engine("sqlite://")
    Base.metadata.create_all(db_engine)
    sessions = sessionmaker(bind=db_engine, expire_on_commit=False)

    rbac = RBACRepository(sessions)
    authorization = AuthorizationService(rbac)

    service = WorkflowHistoryService(
        executions=FakeExecutions(),
        traces=FakeTraces(),
        workflows=FakeWorkflows(),
        projects=FakeProjects(),
        workspaces=FakeWorkspaces(organization_id),
        authorization=authorization,
    )

    return service, rbac


def grant_workflow_read(
    repository,
    *,
    role_id,
    role_name,
    user_id,
    organization_id,
):
    repository.create_role(
        role_id=role_id,
        name=role_name,
    )
    repository.create_permission(
        permission_id=f"{role_id}-read",
        resource="workflow",
        action="read",
    )
    repository.assign_permission_to_role(
        role_id=role_id,
        permission_id=f"{role_id}-read",
    )
    repository.create_membership(
        membership_id=f"{role_id}-membership",
        user_id=user_id,
        organization_id=organization_id,
        role_id=role_id,
    )


def get_detail(service, user_id, roles=frozenset()):
    return service.get_workflow_execution_detail(
        "execution-1",
        current_user=CurrentUser(
            user_id=user_id,
            roles=roles,
        ),
    )


def test_viewer_can_read_execution_in_own_organization():
    service, repository = make_service()

    grant_workflow_read(
        repository,
        role_id="role-viewer",
        role_name="viewer",
        user_id="user-1",
        organization_id="org-1",
    )

    result = get_detail(service, "user-1")

    assert result["execution_id"] == "execution-1"
    assert result["workflow_id"] == "workflow-1"


def test_user_without_membership_cannot_read_execution():
    service, repository = make_service()

    repository.create_role(
        role_id="role-viewer",
        name="viewer",
    )
    repository.create_permission(
        permission_id="viewer-read",
        resource="workflow",
        action="read",
    )
    repository.assign_permission_to_role(
        role_id="role-viewer",
        permission_id="viewer-read",
    )

    with pytest.raises(PermissionError, match="workflow:read"):
        get_detail(
            service,
            "user-1",
            roles=frozenset({"admin"}),
        )


def test_membership_in_wrong_organization_cannot_read_execution():
    service, repository = make_service(
        organization_id="org-1",
    )

    grant_workflow_read(
        repository,
        role_id="role-viewer",
        role_name="viewer",
        user_id="user-1",
        organization_id="org-2",
    )

    with pytest.raises(PermissionError, match="workflow:read"):
        get_detail(service, "user-1")


def test_non_owner_cannot_read_execution():
    service, repository = make_service()

    grant_workflow_read(
        repository,
        role_id="role-viewer",
        role_name="viewer",
        user_id="user-2",
        organization_id="org-1",
    )

    with pytest.raises(ValueError, match="Workflow execution not found"):
        get_detail(service, "user-2")
