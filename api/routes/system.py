"""System API routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.dependencies import get_categories

router = APIRouter(tags=["System"])


@router.get("/health", summary='Health check', description='Return the basic application health status.')
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/healthz", summary='Health check', description='Return the basic application health status using the healthz endpoint.')
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/livez", summary='Liveness check', description='Return the application liveness status.')
def livez() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", summary='Readiness check', description='Return the application readiness status.')
def readyz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics", summary='Prometheus metrics', description='Return application metrics in the Prometheus exposition format.')
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/categories", summary='List categories', description='Return the categories available to the application.')
def categories(
    values: list[str] = Depends(get_categories),
) -> dict[str, list[str]]:
    return {"categories": values}
