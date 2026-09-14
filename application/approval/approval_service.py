import hashlib
import inspect
import secrets
from datetime import datetime, timezone
from typing import Any

from domain.approval import ApprovalDecision, ApprovalRequest
from domain.identity import CurrentUser


class ApprovalService:
    APPROVER_ROLE = "approver"

    def __init__(
        self,
        repository: Any,
        *,
        workflow_executions: Any | None = None,
        workflow_queue: Any | None = None,
        approval_changeset_service: Any | None = None,
    ):
        self.repository = repository
        self.workflow_executions = workflow_executions
        self.workflow_queue = workflow_queue
        self.approval_changeset_service = approval_changeset_service

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
            raise ValueError(
                "EXPIRED is not a caller-selectable approval decision"
            )

        self._authorize_approver(user)

        record = self.repository.get(approval_id)
        if record is None:
            raise ValueError(f"Approval {approval_id} not found")

        if record.decision is not None:
            raise ValueError(
                f"Approval {approval_id} has already been decided"
            )

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
                    "ApprovalChangeSetService is required for "
                    "ChangeSet-backed approvals"
                )

            apply_method = self.approval_changeset_service.apply
            apply_parameters = inspect.signature(
                apply_method
            ).parameters

            if "actor_id" in apply_parameters:
                apply_method(
                    approval_id=approval_id,
                    actor_id=user.user_id,
                )
            else:
                apply_method(
                    approval_id=approval_id,
                )
            return

        if decision == ApprovalDecision.REJECTED:
            self.workflow_executions.cancel(record.execution_id)
            self.repository.update_decision(approval_id, decision)
            return

        self.repository.update_decision(approval_id, decision)

    def list_pending(self) -> list[Any]:
        return self.repository.list_pending()

    def get(self, approval_id: str) -> Any:
        return self.repository.get(approval_id)

