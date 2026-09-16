"""Orchestrate bounded autonomous data operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from domain.agent_memory import ExecutionLearning
from domain.approval import ApprovalRequest
from domain.autonomous_operations import (
    AutonomousDecision,
    AutonomousEvaluation,
)
from domain.identity import CurrentUser
from domain.risk import RiskScore


class AutonomousOperationsOrchestrator:
    """Coordinate the bounded autonomous Detect-to-Learn lifecycle.

    Autonomous execution never invokes capabilities directly. Production
    mutation is performed only through the existing ChangeSet boundary.
    """

    def __init__(
        self,
        *,
        data_health,
        requirements,
        planner,
        risk_service,
        autonomous_ops,
        changeset_service,
        changeset_mutation,
        changeset_rollback,
        changesets,
        datasets,
        approval_service,
        workflow_authoring=None,
        workflow_executions=None,
        simulation_service=None,
        memory_service=None,
        audit_service=None,
    ) -> None:
        self._data_health = data_health
        self._requirements = requirements
        self._planner = planner
        self._risk_service = risk_service
        self._autonomous_ops = autonomous_ops
        self._changeset_service = changeset_service
        self._changeset_mutation = changeset_mutation
        self._changeset_rollback = changeset_rollback
        self._changesets = changesets
        self._datasets = datasets
        self._approval_service = approval_service
        self._workflow_authoring = workflow_authoring
        self._workflow_executions = workflow_executions
        self._simulation_service = simulation_service
        self._memory_service = memory_service
        self._audit_service = audit_service

    @staticmethod
    def _required_blast_radius(plan: Any) -> float:
        """Read blast radius without silently defaulting to zero."""
        metadata = getattr(plan, "metadata", {}) or {}
        risk = metadata.get("risk")

        if not isinstance(risk, dict):
            raise ValueError(
                "Autonomous execution requires risk blast_radius metadata"
            )

        value = risk.get("blast_radius")

        if isinstance(value, bool):
            raise ValueError(
                "Autonomous execution requires a valid blast_radius"
            )

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Autonomous execution requires a valid blast_radius"
            ) from exc

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Autonomous execution requires a valid blast_radius"
            )

        return value

    @staticmethod
    def _simulation_affected_rows(result: Any) -> int:
        """Extract affected rows from a shadow result conservatively."""
        if result is None:
            return 0

        for name in (
            "affected_rows",
            "diff_rows",
            "changed_rows",
        ):
            value = getattr(result, name, None)
            if value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Simulation result has invalid {name}"
                    ) from exc

                if value < 0:
                    raise ValueError(
                        f"Simulation result has invalid {name}"
                    )

                return value

        if isinstance(result, dict):
            for name in (
                "affected_rows",
                "diff_rows",
                "changed_rows",
            ):
                if name in result:
                    try:
                        value = int(result[name])
                    except (TypeError, ValueError) as exc:
                        raise ValueError(
                            f"Simulation result has invalid {name}"
                        ) from exc

                    if value < 0:
                        raise ValueError(
                            f"Simulation result has invalid {name}"
                        )

                    return value

        return 0

    @staticmethod
    def _simulation_changeset_items(result: Any) -> int:
        """Extract candidate change count conservatively."""
        if result is None:
            return 0

        for name in (
            "changeset_items",
            "change_items",
            "diff_items",
        ):
            value = getattr(result, name, None)
            if value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Simulation result has invalid {name}"
                    ) from exc

                if value < 0:
                    raise ValueError(
                        f"Simulation result has invalid {name}"
                    )

                return value

        if isinstance(result, dict):
            for name in (
                "changeset_items",
                "change_items",
                "diff_items",
            ):
                if name in result:
                    try:
                        value = int(result[name])
                    except (TypeError, ValueError) as exc:
                        raise ValueError(
                            f"Simulation result has invalid {name}"
                        ) from exc

                    if value < 0:
                        raise ValueError(
                            f"Simulation result has invalid {name}"
                        )

                    return value

        return 0

    @staticmethod
    def _simulation_confidence(
        result: Any,
        default: float,
    ) -> float:
        """Read simulation confidence when supplied, otherwise use health."""
        value = None

        if result is not None:
            value = getattr(result, "confidence", None)

            if value is None and isinstance(result, dict):
                value = result.get("confidence")

        if value is None:
            value = default

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Autonomous execution requires valid simulation confidence"
            ) from exc

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Autonomous execution requires valid simulation confidence"
            )

        return value

    def run(
        self,
        *,
        request: str,
        workspace_id: str,
        project_id: str,
        user_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_version: str,
        dataset_id: str,
        requested_category: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        requested_intents: tuple[str, ...] = (),
        input_mappings: dict[str, dict[str, str]] | None = None,
        parameters: dict[str, dict[str, object]] | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        """Run one bounded autonomous Detect-to-Learn operation.

        The autonomous path never invokes production capabilities directly.
        Production mutation is performed only through the existing ChangeSet
        boundary.
        """
        if (
            self._workflow_authoring is None
            or self._workflow_executions is None
        ):
            raise RuntimeError(
                "Workflow authoring and execution persistence are required "
                "for autonomous closed-loop execution"
            )

        current_user = CurrentUser(user_id=user_id)

        health, diagnostics = self.detect(
            dataset_id=dataset_id,
            owner_id=user_id,
        )
        remediation_proposals = self.diagnose(
            dataset_id=dataset_id,
            owner_id=user_id,
        )

        plan = self.plan(
            request=request,
            workspace_id=workspace_id,
            user_id=user_id,
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
            requested_intents=requested_intents,
            input_mappings=input_mappings,
            parameters=parameters,
        )

        self._workflow_authoring.save_workflow(
            current_user=current_user,
            workflow_id=workflow_id,
            project_id=project_id,
            name=workflow_name,
            version=workflow_version,
            plan=plan,
        )

        execution_id = str(uuid4())

        self._workflow_executions.create(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            status="CREATED",
            inputs=inputs or {},
            dataset_id=dataset_id,
        )

        simulation_result = self.simulate(
            workflow_id=workflow_id,
            owner_id=user_id,
            inputs=inputs,
            dataset_id=dataset_id,
        )

        health_confidence = float(
            getattr(health, "overall_score", 0.0)
        ) / 100.0

        evaluation = self.govern_simulation(
            plan=plan,
            simulation_result=simulation_result,
            health_confidence=health_confidence,
        )

        changeset = self.prepare_candidate(
            execution_id=execution_id,
        )
        changeset_id = getattr(changeset, "id", None)

        if not changeset_id:
            raise ValueError(
                "Prepared ChangeSet does not contain an id"
            )

        if evaluation.decision == AutonomousDecision.REQUIRE_APPROVAL:
            self._workflow_executions.mark_pending_approval(
                execution_id,
            )

        routed = self.decide_and_route(
            evaluation=evaluation,
            execution_id=execution_id,
            changeset_id=changeset_id,
            requested_by=user_id,
            actor_id=user_id,
        )

        if evaluation.decision == AutonomousDecision.BLOCKED:
            self._workflow_executions.fail(
                execution_id=execution_id,
                error=f"Autonomous operation blocked: {evaluation.reason}",
            )

        if evaluation.decision == AutonomousDecision.AUTO_APPLY:
            if routed.get("verified"):
                self._workflow_executions.complete(
                    execution_id=execution_id,
                    outputs_json=json.dumps(
                        {
                            "changeset_id": changeset_id,
                            "status": "APPLIED",
                            "verified": True,
                        },
                        default=str,
                    ),
                )
                self.record_learning(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    execution_id=execution_id,
                    key="autonomous_operation",
                    value={
                        "decision": evaluation.decision.value,
                        "verified": True,
                        "changeset_id": changeset_id,
                    },
                    context={
                        "dataset_id": dataset_id,
                        "workflow_id": workflow_id,
                    },
                )
            else:
                self._workflow_executions.fail(
                    execution_id=execution_id,
                    error="Autonomous ChangeSet verification failed",
                )

        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "dataset_id": dataset_id,
            "health": health,
            "diagnostics": diagnostics,
            "remediation_proposals": remediation_proposals,
            "evaluation": evaluation,
            "changeset_id": changeset_id,
            "route": routed,
            "verified": routed.get("verified"),
        }

    def evaluate(
        self,
        *,
        dataset_id: str,
        owner_id: str,
        blast_radius: float,
        affected_rows: int,
        changeset_items: int,
        risk_confidence: float,
    ) -> AutonomousEvaluation:
        """Evaluate autonomous governance without mutating production."""
        risk = self._risk_service.evaluate(
            blast_radius=blast_radius,
            confidence=risk_confidence,
        )

        return self._autonomous_ops.evaluate(
            risk_score=risk.risk_score.value,
            blast_radius=blast_radius,
            affected_rows=affected_rows,
            changeset_items=changeset_items,
            confidence=risk.confidence.value,
        )

    def detect(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ):
        """Detect current dataset health and diagnostics."""
        health = self._data_health.get_health(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )
        diagnostics = self._data_health.get_diagnostics(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )
        return health, diagnostics

    def diagnose(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ):
        """Return existing remediation proposals from DataHealthService."""
        return self._data_health.get_remediation_proposals(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )

    def plan(
        self,
        *,
        request: str,
        workspace_id: str,
        user_id: str,
        requested_category: str | None = None,
        requested_capabilities: tuple[str, ...] = (),
        requested_intents: tuple[str, ...] = (),
        input_mappings: dict[str, dict[str, str]] | None = None,
        parameters: dict[str, dict[str, object]] | None = None,
    ):
        """Create a validated plan through the existing agent pipeline."""
        requirement = self._requirements.interpret(
            requested_category=requested_category,
            requested_capabilities=requested_capabilities,
            requested_intents=requested_intents,
            input_mappings=input_mappings,
            parameters=parameters,
            user_request=request,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        return self._planner.plan(requirement)

    def simulate(
        self,
        *,
        workflow_id: str,
        owner_id: str,
        inputs: dict[str, Any] | None = None,
        dataset_id: str | None = None,
    ):
        """Run Shadow Mode through the existing SimulationService."""
        if self._simulation_service is None:
            raise RuntimeError(
                "Simulation service is required for autonomous execution"
            )

        return self._simulation_service.simulate(
            workflow_id=workflow_id,
            current_user=CurrentUser(user_id=owner_id),
            inputs=inputs,
            dataset_id=dataset_id,
        )

    def govern_simulation(
        self,
        *,
        plan: Any,
        simulation_result: Any,
        health_confidence: float,
    ) -> AutonomousEvaluation:
        """Run risk and autonomous policy after simulation."""
        blast_radius = self._required_blast_radius(plan)
        affected_rows = self._simulation_affected_rows(simulation_result)
        changeset_items = self._simulation_changeset_items(
            simulation_result
        )
        confidence = self._simulation_confidence(
            simulation_result,
            health_confidence,
        )

        risk = self._risk_service.evaluate(
            blast_radius=blast_radius,
            confidence=confidence,
        )

        return self._autonomous_ops.evaluate(
            risk_score=risk.risk_score.value,
            blast_radius=blast_radius,
            affected_rows=affected_rows,
            changeset_items=changeset_items,
            confidence=risk.confidence.value,
        )

    def _build_approval_request(
        self,
        *,
        execution_id: str,
        changeset_id: str,
        risk_score: str,
        confidence_score: float,
        requested_by: str,
        expires_at: datetime | None = None,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            approval_id=str(uuid4()),
            execution_id=execution_id,
            changeset_id=changeset_id,
            risk_score=risk_score,
            confidence_score=confidence_score,
            requested_by=requested_by,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

    def request_approval(
        self,
        *,
        execution_id: str,
        changeset_id: str,
        risk_score: RiskScore | str,
        confidence_score: float,
        requested_by: str,
        expires_at: datetime | None = None,
    ) -> str:
        """Create an approval request through the existing service."""
        request = self._build_approval_request(
            execution_id=execution_id,
            changeset_id=changeset_id,
            risk_score=(
                risk_score.value
                if isinstance(risk_score, RiskScore)
                else risk_score
            ),
            confidence_score=confidence_score,
            requested_by=requested_by,
            expires_at=expires_at,
        )
        return self._approval_service.request_approval(request)

    def record_learning(
        self,
        *,
        workspace_id: str,
        user_id: str,
        execution_id: str,
        key: str,
        value: dict[str, object],
        context: dict[str, object] | None = None,
    ):
        """Persist structured autonomous-operation learning."""
        if self._memory_service is None:
            return None

        learning = ExecutionLearning(
            workspace_id=workspace_id,
            user_id=user_id,
            execution_id=execution_id,
            key=key,
            value=value,
            context=context or {},
        )
        return self._memory_service.record_learning(learning)

    def prepare_candidate(
        self,
        *,
        execution_id: str,
    ):
        """Stage an immutable candidate through ChangeSetService."""
        return self._changeset_service.prepare_candidate(
            execution_id=execution_id,
        )

    def apply_candidate(
        self,
        *,
        changeset_id: str,
        actor_id: str | None = None,
    ):
        """Apply only through the production ChangeSet mutation boundary."""
        return self._changeset_mutation.apply(
            changeset_id=changeset_id,
            actor_id=actor_id,
        )

    def verify_candidate(
        self,
        *,
        changeset_id: str,
        dataset_id: str,
    ) -> dict[str, object]:
        """Verify that the dataset pointer matches the applied ChangeSet."""
        changeset = self._changesets.get(changeset_id)
        if changeset is None:
            raise ValueError(f"ChangeSet not found: {changeset_id}")

        if getattr(changeset, "dataset_id", None) != dataset_id:
            raise ValueError(
                "ChangeSet dataset does not match verification dataset"
            )

        dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        storage_key_match = (
            dataset.storage_key == changeset.after_storage_key
        )
        content_hash_match = (
            dataset.content_hash == changeset.after_content_hash
        )

        return {
            "verified": storage_key_match and content_hash_match,
            "storage_key_match": storage_key_match,
            "content_hash_match": content_hash_match,
            "changeset_id": changeset_id,
            "dataset_id": dataset_id,
        }

    def rollback_candidate(
        self,
        *,
        changeset_id: str,
        actor_id: str | None = None,
    ):
        """Rollback an applied candidate through the existing boundary."""
        return self._changeset_rollback.rollback(
            changeset_id=changeset_id,
            actor_id=actor_id,
        )
    def decide_and_route(
        self,
        *,
        evaluation: AutonomousEvaluation,
        execution_id: str,
        changeset_id: str,
        requested_by: str,
        actor_id: str | None = None,
    ):
        """Route an already-prepared candidate according to policy."""
        if evaluation.decision == AutonomousDecision.BLOCKED:
            return {
                "decision": evaluation.decision.value,
                "status": "BLOCKED",
                "reason": evaluation.reason,
                "changeset_id": changeset_id,
            }

        if evaluation.decision == AutonomousDecision.REQUIRE_APPROVAL:
            approval_token = self.request_approval(
                execution_id=execution_id,
                changeset_id=changeset_id,
                risk_score=evaluation.risk_score or "",
                confidence_score=evaluation.confidence or 0.0,
                requested_by=requested_by,
            )
            return {
                "decision": evaluation.decision.value,
                "status": "PENDING_APPROVAL",
                "reason": evaluation.reason,
                "changeset_id": changeset_id,
                "approval_token": approval_token,
            }

        applied = self.apply_candidate(
            changeset_id=changeset_id,
            actor_id=actor_id or requested_by,
        )

        changeset = self._changesets.get(changeset_id)
        if changeset is None:
            raise ValueError(f"ChangeSet not found: {changeset_id}")

        dataset_id = getattr(changeset, "dataset_id", None)
        if not dataset_id:
            raise ValueError(
                "Applied ChangeSet does not contain a dataset_id"
            )

        verification = self.verify_candidate(
            changeset_id=changeset_id,
            dataset_id=dataset_id,
        )

        if verification["verified"]:
            return {
                "decision": evaluation.decision.value,
                "reason": evaluation.reason,
                "changeset_id": changeset_id,
                "applied": applied,
                "status": "APPLIED",
                "verified": True,
                "verification": verification,
            }

        rolled_back = self.rollback_candidate(
            changeset_id=changeset_id,
            actor_id=actor_id or requested_by,
        )

        return {
            "decision": evaluation.decision.value,
            "reason": evaluation.reason,
            "changeset_id": changeset_id,
            "applied": applied,
            "verified": False,
            "verification": verification,
            "status": "ROLLED_BACK",
            "rolled_back": rolled_back,
        }

