from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_approval_service, get_current_user
from application.approval.approval_service import ApprovalService
from domain.approval import ApprovalDecision, ApprovalRequest
from domain.identity import CurrentUser

router = APIRouter(tags=["Approval"])


class ApprovalTokenModel(BaseModel):
    token: str

class ApprovalRequestModel(BaseModel):
    approval_id: str
    execution_id: str
    changeset_id: str
    risk_score: str
    confidence_score: float
    requested_by: str | None = None
    expires_at: datetime | None = None


class ApprovalDecisionModel(BaseModel):
    approval_id: str
    decision: str
    token: str


def _approval_response(record) -> dict:
    return {
        "approval_id": record.approval_id,
        "execution_id": record.execution_id,
        "risk_score": record.risk_score,
        "confidence_score": record.confidence_score,
        "requested_by": record.requested_by,
        "created_at": record.created_at,
        "expires_at": record.expires_at,
        "decision": record.decision,
    }


@router.post("/approval/request", status_code=201, summary='Request approval', description='Create an approval request for an execution or change set with its risk and confidence scores.')
def request_approval(
    request: ApprovalRequestModel,
    current_user: CurrentUser = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service),
):
    approval_req = ApprovalRequest(
        approval_id=request.approval_id,
        execution_id=request.execution_id,
        changeset_id=request.changeset_id,
        risk_score=request.risk_score,
        confidence_score=request.confidence_score,
        requested_by=current_user.user_id,
        created_at=datetime.now(timezone.utc),
        expires_at=request.expires_at,
    )

    try:
        token = approval_service.request_approval(approval_req)

        return {
            "status": "request_created",
            "approval_id": request.approval_id,
            "token": token,
        }
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/approval/decision", summary='Record approval decision', description='Record an approval decision using the supplied approval identifier, decision, and authorization token.')
def decide_approval(
    decision: ApprovalDecisionModel,
    current_user: CurrentUser = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service),
):
    try:
        approval_service.decide(
            approval_id=decision.approval_id,
            decision=ApprovalDecision(decision.decision),
            user=current_user,
            token=decision.token,
        )
        return {"status": "decision_recorded"}
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/approvals/pending", summary='List pending approvals', description='Return approval requests that are currently pending decision.')
def list_pending_approvals(
    approval_service: ApprovalService = Depends(get_approval_service),
    current_user=Depends(get_current_user),
):
    return [
        _approval_response(record)
        for record in approval_service.list_pending(user=current_user)
    ]


@router.post("/approvals/{approval_id}/approve", summary='Approve request', description='Approve a pending approval request using its approval identifier and authorization token.')
def approve(
    approval_id: str,
    body: ApprovalTokenModel,
    current_user: CurrentUser = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service),
):
    try:
        approval_service.decide(
            approval_id=approval_id,
            decision=ApprovalDecision.APPROVED,
            user=current_user,
            token=body.token,
        )
        return {
            "status": "decision_recorded",
            "approval_id": approval_id,
            "decision": ApprovalDecision.APPROVED.value,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/approvals/{approval_id}/reject", summary='Reject request', description='Reject a pending approval request using its approval identifier and authorization token.')
def reject(
    approval_id: str,
    body: ApprovalTokenModel,
    current_user: CurrentUser = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service),
):
    try:
        approval_service.decide(
            approval_id=approval_id,
            decision=ApprovalDecision.REJECTED,
            user=current_user,
            token=body.token,
        )
        return {
            "status": "decision_recorded",
            "approval_id": approval_id,
            "decision": ApprovalDecision.REJECTED.value,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

