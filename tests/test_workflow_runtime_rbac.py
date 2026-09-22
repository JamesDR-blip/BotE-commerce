from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from domain.identity import CurrentUser
from repositories.rbac import RBACRepository
from services.authorization import AuthorizationService
from application.workflows.runtime_service import WorkflowRuntimeService


class FakeEngine:
    def __init__(self) -> None:
        self.called = False

    def execute(
        self,
        *,
        workflow_id,
        execution_id,
        inputs,
        dataset_id,
    ):
        self.called = True
        return SimpleNamespace(
            execution_id=execution_id,
            workflow_id=workflow_id,
        )


class FakeWorkflowRepository:
    def get_for_owner(self, *, workflow_id, owner_id):
        return SimpleNamespace(
            project_id="project-1",
        )


class FakeProjectRepository:
    def get_for_owner(self, *, project_id, owner_id):
        return SimpleNamespace(
            workspace_id="workspace-1",
        )


class FakeWorkspaceRepository:
    def __init__(self, organization_id: str) -> None:
        self.organization_id = organization_id

    def get_for_owner(self, *, workspace_id, owner_id):
        return SimpleNamespace(
            organization_id=self.organization_id,
        )


def make_runtime(
    *,
    organization_id: str = "org-1",
):
    engine = FakeEngine()

    db_engine = create_engine("sqlite://")
    Base.metadata.create_all(db_engine)
    sessions = sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
    )

    rbac = RBACRepository(sessions)
    authorization = AuthorizationService(rbac)

    service = WorkflowRuntimeService(
        workflow_engine=lambda: engine,
        workflow_history=lambda: None,
        workflows=lambda: FakeWorkflowRepository(),
        projects=lambda: FakeProjectRepository(),
        workspaces=lambda: FakeWorkspaceRepository(
            organization_id
        ),
        authorization=authorization,
    )

    return service, engine, rbac


def grant_permission(
    repository: RBACRepository,
    *,
    role_id: str,
    role_name: str,
    user_id: str,
    organization_id: str,
):
    repository.create_role(
        role_id=role_id,
        name=role_name,
    )
    repository.create_permission(
        permission_id=f"{role_id}-execute",
        resource="workflow",
        action="execute",
    )
    repository.assign_permission_to_role(
        role_id=role_id,
        permission_id=f"{role_id}-execute",
    )
    repository.create_membership(
        membership_id=f"{role_id}-membership",
        user_id=user_id,
        organization_id=organization_id,
        role_id=role_id,
    )


def execute(service, user_id: str, roles=frozenset()):
    return service.execute(
        current_user=CurrentUser(
            user_id=user_id,
            roles=roles,
        ),
        workflow_id="workflow-1",
        inputs={},
    )


def test_viewer_cannot_execute_workflow():
    service, engine, repository = make_runtime()

    repository.create_role(
        role_id="role-viewer",
        name="viewer",
    )
    repository.create_permission(
        permission_id="permission-workflow-read",
        resource="workflow",
        action="read",
    )
    repository.assign_permission_to_role(
        role_id="role-viewer",
        permission_id="permission-workflow-read",
    )
    repository.create_membership(
        membership_id="viewer-membership",
        user_id="user-1",
        organization_id="org-1",
        role_id="role-viewer",
    )

    with pytest.raises(
        PermissionError,
        match="workflow:execute",
    ):
        execute(service, "user-1")

    assert engine.called is False


def test_data_engineer_can_execute_in_own_organization():
    service, engine, repository = make_runtime()

    grant_permission(
        repository,
        role_id="role-engineer",
        role_name="data_engineer",
        user_id="user-1",
        organization_id="org-1",
    )

    result = execute(service, "user-1")

    assert result.workflow_id == "workflow-1"
    assert engine.called is True


def test_admin_role_on_current_user_without_membership_cannot_execute():
    service, engine, repository = make_runtime()

    result = repository.list_permission_keys(
        user_id="user-1",
        organization_id="org-1",
    )

    assert result == frozenset()

    with pytest.raises(
        PermissionError,
        match="workflow:execute",
    ):
        execute(
            service,
            "user-1",
            roles=frozenset({"admin"}),
        )

    assert engine.called is False


def test_membership_in_wrong_organization_cannot_execute():
    service, engine, repository = make_runtime(
        organization_id="org-1",
    )

    grant_permission(
        repository,
        role_id="role-engineer",
        role_name="data_engineer",
        user_id="user-1",
        organization_id="org-2",
    )

    with pytest.raises(
        PermissionError,
        match="workflow:execute",
    ):
        execute(service, "user-1")

    assert engine.called is False
