"""FastAPI application factory."""
from __future__ import annotations
import logging

from api.routes import (
    data_router,
    datasets_router,
    executions_router,
    health_router,
    rules_router,
    studio_router,
    system_router,
    workflows_router,
)
from configs.settings import Settings

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.container import Container
from infrastructure.observability.logging import configure_logging, instrument_fastapi

logger = logging.getLogger(__name__)


def _internal_server_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unexpected_application_error",
        extra={
            "event": "unexpected_application_error",
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    logger.info("application_configured", extra={"event": "application_configured", "environment": settings.environment})
    container = Container(settings)
    quality_service = container.quality_service
    app = FastAPI(title="AI Studio E-commerce Platform", version="1.0.0")
    app.include_router(data_router)
    app.include_router(datasets_router)
    app.include_router(executions_router)
    app.include_router(health_router)
    app.include_router(rules_router)
    app.include_router(studio_router)
    app.include_router(system_router)
    app.include_router(workflows_router)
    app.add_exception_handler(Exception, _internal_server_error)
    app.state.container = container
    app.state.authentication = container.authentication
    app.state.quality_service = quality_service
    app.state.data_health = container.data_health
    app.state.data_operations = container.data_operations
    app.state.mapping_service = container.mapping
    app.state.workflow_history = container.workflow_history
    app.state.workflow_authoring = container.workflow_authoring
    app.state.dataset_service = container.dataset_service
    app.state.workspace_projects = container.workspace_projects
    app.state.workflow_runtime = container.workflow_runtime
    app.state.execution_repository = container.executions
    app.state.execution_trace_repository = container.execution_traces
    app.state.upload_reader = container.uploads
    app.state.rule_intelligence = container.rule_intelligence
    app.state.categories = container.registry.categories()
    instrument_fastapi(app)
    return app

