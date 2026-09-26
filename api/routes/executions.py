"""Execution, history, and report API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.dependencies import (
    get_execution_repository,
    get_execution_trace_repository,
)
from schemas.responses import (
    CapabilityTraceResponse,
    ExecutionDetailResponse,
    HistoryResponse,
)
from repositories.executions import ExecutionRepository
from repositories.execution_traces import ExecutionTraceRepository


router = APIRouter(tags=["Executions"])


@router.get("/executions", summary='List execution history', description='Return execution history entries, limited by the requested result count.')
def history(
    limit: int = 50,
    executions: ExecutionRepository = Depends(
        get_execution_repository
    ),
) -> list[dict[str, str | float]]:
    return _history_items(executions, limit)


@router.get("/history", response_model=HistoryResponse, summary='List execution history', description='Compatibility endpoint that returns execution history in the HistoryResponse format.')
def history_alias(
    limit: int = 50,
    executions: ExecutionRepository = Depends(
        get_execution_repository
    ),
) -> HistoryResponse:
    return HistoryResponse(
        items=_history_items(executions, limit)
    )


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionDetailResponse,
     summary='Get execution detail',
     description='Return execution details together with the associated execution trace information.'
 )
def execution_detail(
    execution_id: str,
    executions: ExecutionRepository = Depends(
        get_execution_repository
    ),
    traces_repository: ExecutionTraceRepository = Depends(
        get_execution_trace_repository
    ),
) -> ExecutionDetailResponse:
    execution = executions.get(execution_id)

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}",
        )

    traces = traces_repository.list_by_execution(
        execution_id
    )

    return ExecutionDetailResponse(
        execution_id=execution.id,
        category=execution.category,
        status=execution.status,
        health_score=execution.health_score,
        created_at=execution.created_at,
        requirement_json=execution.requirement_json,
        plan_json=execution.plan_json,
        planner_version=execution.planner_version,
        traces=[
            CapabilityTraceResponse(
                capability_id=trace.capability_id,
                capability_version=trace.capability_version,
                status=trace.status,
                started_at=trace.started_at,
                finished_at=trace.finished_at,
            )
            for trace in traces
        ],
    )


@router.get(
    "/executions/{execution_id}/reports/{report_format}",
     summary='Download execution report',
     description='Generate and download a report for the specified execution and report format.'
 )
def download_report(
    execution_id: str,
    report_format: str,
    executions: ExecutionRepository = Depends(
        get_execution_repository
    ),
) -> FileResponse:
    return _download_report(
        executions,
        execution_id,
        report_format,
    )


@router.get("/report/{execution_id}/{report_format}", summary='Download execution report', description='Compatibility endpoint for downloading a report for the specified execution and report format.')
def report_alias(
    execution_id: str,
    report_format: str,
    executions: ExecutionRepository = Depends(
        get_execution_repository
    ),
) -> FileResponse:
    return _download_report(
        executions,
        execution_id,
        report_format,
    )


def _history_items(
    executions: ExecutionRepository,
    limit: int,
) -> list[dict[str, str | float]]:
    return [
        {
            "id": item.id,
            "category": item.category,
            "health_score": item.health_score,
            "created_at": item.created_at.isoformat(),
        }
        for item in executions.history(
            min(max(limit, 1), 100)
        )
    ]


def _download_report(
    executions: ExecutionRepository,
    execution_id: str,
    report_format: str,
) -> FileResponse:
    if report_format not in {
        "excel",
        "html",
        "pdf",
        "json",
    }:
        raise HTTPException(
            status_code=404,
            detail="Unsupported report format",
        )

    path = executions.report_path(
        execution_id,
        report_format,
    )

    if not path or not Path(path).is_file():
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return FileResponse(
        path,
        filename=(
            f"data-quality-report."
            f"{Path(path).suffix.lstrip('.')}"
        ),
    )