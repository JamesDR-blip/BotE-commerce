from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.container import Container, build_container
from domain.risk_evaluation import RiskEvaluationResult

router = APIRouter(tags=["Risk"])

class EvaluateRequest(BaseModel):
    blast_radius: float
    confidence: float

class EvaluateResponse(BaseModel):
    risk_score: str
    confidence: float
    approval_required: bool

def get_container() -> Container:
    return build_container()

@router.post("/risk/evaluate", response_model=EvaluateResponse, summary='Evaluate risk', description='Evaluate risk from the supplied blast radius and confidence and indicate whether approval is required.')
def evaluate_risk(request: EvaluateRequest, container: Container = Depends(get_container)):
    try:
        result: RiskEvaluationResult = container.risk_service.evaluate(request.blast_radius, request.confidence)
        return EvaluateResponse(
            risk_score=result.risk_score.value,
            confidence=result.confidence.value,
            approval_required=result.approval_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
