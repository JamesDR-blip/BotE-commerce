import hashlib
import inspect
import secrets
from datetime import datetime, timezone
from typing import Any

from domain.approval import ApprovalDecision, ApprovalRequest
from domain.authorization import Permission
from domain.identity import CurrentUser
from services.authorization import AuthorizationService


class ApprovalService:
    APPROVER_ROLE = "approver"

    def __init__(
        self,
        repository: Any,
        *,
        workflow_executions: Any | None = None,
        workflow_queue: Any | None = None,
        approval_changeset_service: Any | None = None,
        workflows: Any | None = None,
        projects: Any | None = None,
        workspaces: Any | None = None,
        authorization: AuthorizationService | None = None,
    ):
        self.repository = repository
        self.workflow_executions = workflow_executions
        self.workflow_queue = workflow_queue
        self.approval_changeset_service = approval_changeset_service
        self.workflows = workflows
        self.projects = projects
        self.workspaces = workspaces
        self.authorization = authorization

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def _generate_token(cls) -> tuple[str, str]:
        token = secrets.token_urlsafe(32)
        return token, cls._hash_token(token)

    def request_approval(self, request: ApprovalRequest) -> str:
        token, token_hash = self._generate_token()
        self.repository.create(request, token_hash=token_hash)
        return token

    def _authorize_approver(self, user: CurrentUser) -> None:
        if self.APPROVER_ROLE not in user.roles:
            raise PermissionError(
                "Approver role required for approval decisions"
            )

    def _organization_id_for_approval(
        self,
        *,
        approval: Any,
    ) -> str:
        if (
            self.workflow_executions is None
            or self.workflows is None
            or self.projects is None
            or self.workspaces is None
        ):
            raise ValueError(
                "Approval authorization dependencies are not configured"
            )

        execution = self.workflow_executions.get(approval.execution_id)
        if execution is None:
            raise ValueError(
                f"Workflow execution {approval.execution_id} not found"
            )

        workflow = self.workflows.get(execution.workflow_id)
        if workflow is None:
            raise ValueError(
                f"Workflow {execution.workflow_id} not found"
            )

        project = self.projects.get(workflow.project_id)
        if project is None:
            raise ValueError(
                f"Project {workflow.project_id} not found"
            )

        workspace = self.workspaces.get(project.workspace_id)
        if workspace is None:
            raise ValueError(
                f"Workspace {project.workspace_id} not found"
            )

        if workspace.organization_id is None:
            raise ValueError(
                f"Workspace {workspace.id} is not assigned to an organization"
            )

        return workspace.organization_id


    def _authorize_decision(
        self,
        *,
        user: CurrentUser,
        approval: Any,
    ) -> str | None:
        if self.authorization is None:
            return None

        organization_id = self._organization_id_for_approval(
            approval=approval,
        )
        self.authorization.authorize(
            user=user,
            resource="approval",
            action="decide",
            organization_id=organization_id,
        )
        return organization_id

    def _authorize_read(
        self,
        *,
        user: CurrentUser,
        approval: Any,
    ) -> str | None:
        if self.authorization is None:
            return None

        organization_id = self._organization_id_for_approval(
            approval=approval,
        )
        self.authorization.authorize(
            user=user,
            resource="approval",
            action="read",
            organization_id=organization_id,
        )
        return organization_id

    def _validate_token(self, record: Any, token: str) -> None:
        if not token:
            raise ValueError("Approval token is required")
        if not getattr(record, "token_hash", None):
            raise ValueError("Approval token is not available for this approval")
        token_hash = self._hash_token(token)
        if not secrets.compare_digest(record.token_hash, token_hash):
            raise ValueError("Invalid approval token")

    def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        *,
        user: CurrentUser,
        token: str,
    ) -> None:
        if decision == ApprovalDecision.EXPIRED:
            raise ValueError("EXPIRED is not a caller-selectable approval decision")

        self._authorize_approver(user)

        record = self.repository.get(approval_id)
        if record is None:
            raise ValueError(f"Approval {approval_id} not found")

        self._authorize_decision(
            user=user,
            approval=record,
        )

        if record.decision is not None:
            raise ValueError(f"Approval {approval_id} has already been decided")

        self._validate_token(record, token)

        if record.expires_at is not None:
            expires_at = record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                self.repository.update_decision(
                    approval_id,
                    ApprovalDecision.EXPIRED,
                )
                raise ValueError(f"Approval {approval_id} has expired")

        if self.workflow_executions is None:
            self.repository.update_decision(approval_id, decision)
            return

        if decision == ApprovalDecision.APPROVED:
            if self.approval_changeset_service is None:
                raise RuntimeError(
                    "ApprovalChangeSetService is required for ChangeSet-backed approvals"
                )

            apply_method = self.approval_changeset_service.apply
            apply_parameters = inspect.signature(apply_method).parameters

            if "actor_id" in apply_parameters:
                apply_method(
                    approval_id=approval_id,
                    actor_id=user.user_id,
                )
            else:
                apply_method(approval_id=approval_id)
            return

        if decision == ApprovalDecision.REJECTED:
            self.workflow_executions.cancel(record.execution_id)
            self.repository.update_decision(
                approval_id,
                decision,
            )
            return

        self.repository.update_decision(approval_id, decision)

    def list_pending(
        self,
        *,
        user: CurrentUser | None = None,
    ) -> list[Any]:
        if self.authorization is None or user is None:
            return self.repository.list_pending()

        if self.authorization.rbac_repository is None:
            return []

        organization_ids = (
            self.authorization.rbac_repository.list_organization_ids_for_user(
                user_id=user.user_id,
            )
        )

        approvals: list[Any] = []

        for organization_id in organization_ids:
            decision = self.authorization.decide(
                user=user,
                permission=Permission(
                    resource="approval",
                    action="read",
                ),
                organization_id=organization_id,
            )

            if not decision.allowed:
                continue

            approvals.extend(
                self.repository.list_pending_for_organization(
                    organization_id=organization_id,
                )
            )

        return approvals

    def get_for_execution(
        self,
        execution_id: str,
        *,
        user: CurrentUser | None = None,
    ) -> Any | None:
        if self.authorization is None or user is None:
            approvals = self.repository.get_by_execution_id(execution_id)
        else:
            if self.workflow_executions is None:
                raise ValueError(
                    "Approval authorization dependencies are not configured"
                )

            execution = self.workflow_executions.get(execution_id)
            if execution is None:
                return None

            workflow = self.workflows.get(execution.workflow_id)
            if workflow is None:
                return None

            project = self.projects.get(workflow.project_id)
            if project is None:
                return None

            workspace = self.workspaces.get(project.workspace_id)
            if workspace is None or workspace.organization_id is None:
                return None

            self.authorization.authorize(
                user=user,
                resource="approval",
                action="read",
                organization_id=workspace.organization_id,
            )

            approvals = (
                self.repository.get_by_execution_id_for_organization(
                    execution_id,
                    organization_id=workspace.organization_id,
                )
            )

        for approval in approvals:
            if approval.decision is None:
                return approval

        return None

    def get(
        self,
        approval_id: str,
        *,
        user: CurrentUser | None = None,
    ) -> Any:
        if self.authorization is None or user is None:
            return self.repository.get(approval_id)

        record = self.repository.get(approval_id)
        if record is None:
            return None

        organization_id = self._organization_id_for_approval(
            approval=record,
        )

        self.authorization.authorize(
            user=user,
            resource="approval",
            action="read",
            organization_id=organization_id,
        )

        return record