"""Data Health Command Center API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import (
    get_current_user,
    get_data_health_service,
)
from application.quality.data_health_service import DataHealthService
from domain.identity import CurrentUser
from schemas.responses import (
    DatasetHealthResponse,
    DiagnosticsResponse,
    HealthMetricResponse,
    HealthMetricsResponse,
    IssueDiagnosticResponse,
    RemediationProposalResponse,
)

router = APIRouter()


@router.get(
    "/health-metrics",
    response_model=HealthMetricsResponse,
)
def get_health_metrics(
    project_id: str = Query(...),
    service: DataHealthService = Depends(get_data_health_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> HealthMetricsResponse:
    items = service.get_health_metrics(
        project_id=project_id,
        owner_id=current_user.user_id,
    )

    return HealthMetricsResponse(
        project_id=project_id,
        items=[
            DatasetHealthResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                aggregate=health.aggregate,
                metrics=[
                    HealthMetricResponse(
                        dimension=metric.dimension.value,
                        score=metric.score,
                        assessed=metric.assessed,
                    )
                    for metric in health.metrics
                ],
            )
            for dataset, health in items
        ],
    )


@router.get(
    "/diagnostics/{dataset_id}",
    response_model=DiagnosticsResponse,
)
def get_diagnostics(
    dataset_id: str,
    service: DataHealthService = Depends(get_data_health_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DiagnosticsResponse:
    try:
        diagnostics = service.get_diagnostics(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )
        proposals = service.get_remediation_proposals(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {dataset_id}",
        ) from exc

    return DiagnosticsResponse(
        dataset_id=dataset_id,
        diagnostics=[
            IssueDiagnosticResponse(
                code=diagnostic.code,
                field=diagnostic.field,
                message=diagnostic.message,
                severity=diagnostic.severity,
                count=diagnostic.count,
            )
            for diagnostic in diagnostics
        ],
        remediation_proposals=[
            RemediationProposalResponse(
                id=proposal.id,
                diagnostic_code=proposal.diagnostic_code,
                action=proposal.action,
                rationale=proposal.rationale,
                severity=proposal.severity,
                status=proposal.status,
            )
            for proposal in proposals
        ],
    )
