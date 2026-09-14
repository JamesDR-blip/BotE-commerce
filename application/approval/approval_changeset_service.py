"""Atomic approval -> ChangeSet production application."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from domain.approval import ApprovalDecision


class ApprovalChangeSetService:
    """Atomically applies an approved ChangeSet and closes its execution."""

    def __init__(
        self,
        *,
        sessions: Callable[[], Any],
        approvals: Any,
        changesets: Any,
        workflow_executions: Any,
    ) -> None:
        self._sessions = sessions
        self._approvals = approvals
        self._changesets = changesets
        self._workflow_executions = workflow_executions

    def apply(
        self,
        *,
        approval_id: str,
    ) -> None:
        with self._sessions() as session:
            with session.begin():
                approval = self._approvals.get_in_transaction(
                    session,
                    approval_id,
                )

                if approval is None:
                    raise ValueError(
                        f"Approval {approval_id} not found"
                    )

                if approval.decision is not None:
                    raise ValueError(
                        f"Approval {approval_id} has already been decided"
                    )

                changeset = self._changesets.get_record_in_transaction(
                    session,
                    approval.changeset_id,
                )

                if changeset is None:
                    raise ValueError(
                        "ChangeSet not found: "
                        f"{approval.changeset_id}"
                    )

                if changeset.execution_id != approval.execution_id:
                    raise ValueError(
                        "Approval and ChangeSet execution IDs do not match"
                    )

                execution = self._workflow_executions.get_in_transaction(
                    session,
                    approval.execution_id,
                )

                if execution is None:
                    raise ValueError(
                        "Workflow execution not found: "
                        f"{approval.execution_id}"
                    )

                if execution.dataset_id != changeset.dataset_id:
                    raise ValueError(
                        "Workflow execution and ChangeSet dataset IDs do not match"
                    )

                if execution.workflow_id != changeset.workflow_id:
                    raise ValueError(
                        "Workflow execution and ChangeSet workflow IDs do not match"
                    )

                if execution.workflow_version != changeset.workflow_version:
                    raise ValueError(
                        "Workflow execution and ChangeSet workflow versions do not match"
                    )

                if changeset.status != "PREPARED":
                    raise ValueError(
                        "Only PREPARED ChangeSets can be approved: "
                        f"{changeset.id} ({changeset.status})"
                    )

                self._changesets.apply_in_transaction(
                    session,
                    changeset_id=changeset.id,
                    expected_before_storage_key=(
                        changeset.before_storage_key
                    ),
                )

                self._approvals.update_decision_in_transaction(
                    session,
                    approval_id,
                    ApprovalDecision.APPROVED,
                )

                self._workflow_executions.complete_after_approval_in_transaction(
                    session,
                    execution_id=approval.execution_id,
                    outputs_json=json.dumps(
                        {
                            "changeset_id": changeset.id,
                            "status": "APPLIED",
                        }
                    ),
                )
