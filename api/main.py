"""FastAPI application factory."""
from __future__ import annotations
import logging
import json
from uuid import uuid4
from pathlib import Path
from schemas.responses import (
    ExecutionDetailResponse,
    ExtractionResponse,
    HistoryResponse,
    MappingResponse,
    TabularPreviewResponse,
    UploadResponse,
    ValidationResponse,
    CapabilityTraceResponse,
    WorkspaceResponse,
    ProjectResponse,
    DatasetResponse,
    WorkflowResponse,
    WorkflowVersionResponse,
    WorkflowExecutionResponse,
    WorkflowExecutionDetailResponse,
)
from schemas.requests import (
    WorkspaceCreateRequest,
    ProjectCreateRequest,
    DatasetCreateRequest,
    WorkflowCreateRequest,
    WorkflowVersionCreateRequest,
    WorkflowExecutionRequest,
)
from configs.settings import Settings
from domain.exceptions import ValidationRequestError
from api.dependencies import (
    get_container,
    get_data_operations,
    get_mapping_service,
    get_quality_service,
)
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from services.container import Container
from services.logging import configure_logging, instrument_fastapi
from services.quality_service import QualityService
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService
from services.execution_plan_serializer import ExecutionPlanSerializer

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
    container = Container(settings);service = container.quality_service
    app = FastAPI(title="AI Studio E-commerce Platform", version="1.0.0")
    app.add_exception_handler(Exception, _internal_server_error)
    app.state.container = container
    app.state.quality_service = service
    app.state.data_operations = container.data_operations
    app.state.mapping_service = container.mapping
    @app.get("/health")
    def health() -> dict[str, str]: return {"status": "ok"}
    @app.get("/categories")
    def categories(current: Container = Depends(get_container)) -> dict[str, list[str]]: return {"categories": current.registry.categories()}
    @app.get("/executions")
    def history(limit: int = 50, current: Container = Depends(get_container)) -> list[dict[str, str | float]]:
        return _history_items(current, limit)
    
    @app.get("/history", response_model=HistoryResponse)
    def history_alias(limit: int = 50, current: Container = Depends(get_container)) -> HistoryResponse:
        return HistoryResponse(items=_history_items(current, limit))

    @app.get(
        "/executions/{execution_id}",
        response_model=ExecutionDetailResponse,
    )
    def execution_detail(
        execution_id: str,
        current: Container = Depends(get_container),
    ) -> ExecutionDetailResponse:
        execution = current.executions.get(execution_id)

        if execution is None:
            raise HTTPException(
                status_code=404,
                detail=f"Execution not found: {execution_id}",
            )

        traces = current.execution_traces.list_by_execution(
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

    @app.get("/executions/{execution_id}/reports/{report_format}")
    def download_report(execution_id: str, report_format: str, current: Container = Depends(get_container)) -> FileResponse:
        return _download_report(current, execution_id, report_format)
    @app.get("/report/{execution_id}/{report_format}")
    def report_alias(execution_id: str, report_format: str, current: Container = Depends(get_container)) -> FileResponse:
        return _download_report(current, execution_id, report_format)
    @app.post("/upload", response_model=UploadResponse)
    async def upload(file: UploadFile = File(...), current: Container = Depends(get_container)) -> UploadResponse:
        frame = await _read_frame(file, current)
        return UploadResponse(filename=file.filename or "", rows=len(frame), columns=[str(column) for column in frame.columns])
    @app.post("/clean", response_model=TabularPreviewResponse)
    async def clean(file: UploadFile = File(...), category: str | None = Form(None), operations: DataOperationsService = Depends(get_data_operations), current: Container = Depends(get_container)) -> TabularPreviewResponse:
        frame = await _read_frame(file, current)
        detected, cleaned = operations.clean(frame, category)
        return _preview(detected, cleaned)
    @app.post("/extract", response_model=ExtractionResponse)
    async def extract(file: UploadFile = File(...), operations: DataOperationsService = Depends(get_data_operations), current: Container = Depends(get_container)) -> ExtractionResponse:
        frame = await _read_frame(file, current)
        return ExtractionResponse(records=[{"row": index + 2, "attributes": item.as_dict()} for index, item in enumerate(operations.extract(frame))])
    @app.post("/mapping", response_model=MappingResponse)
    async def mapping(file: UploadFile = File(...), target_columns: str | None = Form(None), mappings: MappingService = Depends(get_mapping_service), current: Container = Depends(get_container)) -> MappingResponse:
        frame = await _read_frame(file, current)
        targets = [value.strip() for value in target_columns.split(",") if value.strip()] if target_columns else None
        suggested, unmapped = mappings.suggest(frame.columns, targets)
        return MappingResponse(mappings=suggested, unmapped_columns=unmapped)
    @app.post("/validate", response_model=ValidationResponse)
    async def validate_alias(file: UploadFile = File(...), category: str | None = Form(None), current: Container = Depends(get_container), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
        return await _validate_upload(file, category, current, quality)
    @app.post("/validations", response_model=ValidationResponse)
    async def validate(file: UploadFile = File(...), category: str | None = Form(None), current: Container = Depends(get_container), quality: QualityService = Depends(get_quality_service)) -> ValidationResponse:
        return await _validate_upload(file, category, current, quality)

    @app.post(
        "/workspaces",
        response_model=WorkspaceResponse,
    )
    def create_workspace(
        payload: WorkspaceCreateRequest,
        current: Container = Depends(get_container),
    ) -> WorkspaceResponse:
        workspace = current.studio.create_workspace(
            workspace_id=payload.id,
            name=payload.name,
        )

        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
        )


    @app.get(
        "/workspaces/{workspace_id}",
        response_model=WorkspaceResponse,
    )
    def get_workspace(
        workspace_id: str,
        current: Container = Depends(get_container),
    ) -> WorkspaceResponse:
        workspace = current.studio.get_workspace(
            workspace_id
        )

        if workspace is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workspace not found: {workspace_id}",
            )

        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
        )

    @app.post(
        "/projects",
        response_model=ProjectResponse,
    )
    def create_project(
        payload: ProjectCreateRequest,
        current: Container = Depends(get_container),
    ) -> ProjectResponse:
        project = current.studio.create_project(
            project_id=payload.id,
            workspace_id=payload.workspace_id,
            name=payload.name,
            description=payload.description,
        )

        return ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )


    @app.get(
        "/projects/{project_id}",
        response_model=ProjectResponse,
    )
    def get_project(
        project_id: str,
        current: Container = Depends(get_container),
    ) -> ProjectResponse:
        project = current.studio.projects.get(
            project_id
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}",
            )

        return ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )


    @app.get(
        "/workspaces/{workspace_id}/projects",
        response_model=list[ProjectResponse],
    )
    def list_projects(
        workspace_id: str,
        current: Container = Depends(get_container),
    ) -> list[ProjectResponse]:
        projects = current.studio.list_projects(
            workspace_id
        )

        return [
            ProjectResponse(
                id=project.id,
                workspace_id=project.workspace_id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
            )
            for project in projects
        ]

    @app.post(
        "/datasets",
        response_model=DatasetResponse,
    )
    def create_dataset(
        payload: DatasetCreateRequest,
        current: Container = Depends(get_container),
    ) -> DatasetResponse:

        dataset = current.studio.create_dataset(
            dataset_id=payload.id,
            project_id=payload.project_id,
            name=payload.name,
            source_type=payload.source_type,
            metadata=payload.metadata,
        )

        return DatasetResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            name=dataset.name,
            source_type=dataset.source_type,
            metadata=dataset.metadata_json,
            created_at=dataset.created_at,
        )


    @app.get(
        "/datasets/{dataset_id}",
        response_model=DatasetResponse,
    )
    def get_dataset(
        dataset_id: str,
        current: Container = Depends(get_container),
    ) -> DatasetResponse:

        dataset = current.studio.get_dataset(
            dataset_id
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found: {dataset_id}",
            )

        return DatasetResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            name=dataset.name,
            source_type=dataset.source_type,
            metadata=dataset.metadata_json,
            created_at=dataset.created_at,
        )

    @app.get(
        "/projects/{project_id}/datasets",
        response_model=list[DatasetResponse],
    )
    def list_datasets(
        project_id: str,
        current: Container = Depends(get_container),
    ) -> list[DatasetResponse]:

        datasets = current.studio.list_datasets(
            project_id
        )

        return [
            DatasetResponse(
                id=dataset.id,
                project_id=dataset.project_id,
                name=dataset.name,
                source_type=dataset.source_type,
                metadata=dataset.metadata_json,
                created_at=dataset.created_at,
            )
            for dataset in datasets
        ]
    @app.post(
        "/workflows",
        response_model=WorkflowResponse,
    )
    def create_workflow(
        payload: WorkflowCreateRequest,
        current: Container = Depends(get_container),
    ) -> WorkflowResponse:

        plan = _execution_plan_from_payload(
            payload.plan
        )

        workflow = current.studio.save_workflow(
            workflow_id=payload.id,
            project_id=payload.project_id,
            name=payload.name,
            version=payload.version,
            plan=plan,
        )

        return WorkflowResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.name,
            active_version=workflow.active_version,
            status=workflow.status,
            created_at=workflow.created_at,
        )

    @app.get(
        "/workflows/{workflow_id}",
        response_model=WorkflowResponse,
    )
    def get_workflow(
        workflow_id: str,
        current: Container = Depends(get_container),
    ) -> WorkflowResponse:

        workflow = current.studio.get_workflow(
            workflow_id
        )

        if workflow is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}",
            )

        return WorkflowResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.name,
            active_version=workflow.active_version,
            status=workflow.status,
            created_at=workflow.created_at,
        )

    @app.get(
        "/projects/{project_id}/workflows",
        response_model=list[WorkflowResponse],
    )
    def list_workflows(
        project_id: str,
        current: Container = Depends(get_container),
    ) -> list[WorkflowResponse]:

        workflows = current.studio.list_workflows(
            project_id
        )

        return [
            WorkflowResponse(
                id=workflow.id,
                project_id=workflow.project_id,
                name=workflow.name,
                active_version=workflow.active_version,
                status=workflow.status,
                created_at=workflow.created_at,
            )
            for workflow in workflows
        ]

    @app.post(
        "/workflows/{workflow_id}/versions",
        response_model=WorkflowVersionResponse,
    )
    def create_workflow_version(
        workflow_id: str,
        payload: WorkflowVersionCreateRequest,
        current: Container = Depends(get_container),
    ) -> WorkflowVersionResponse:

        plan = _execution_plan_from_payload(
            payload.plan
        )

        try:
            version = current.studio.create_workflow_version(
                workflow_id=workflow_id,
                version=payload.version,
                plan=plan,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        return WorkflowVersionResponse(
            id=version.id,
            workflow_id=version.workflow_id,
            version=version.version,
            plan=json.loads(version.plan_json),
            created_at=version.created_at,
        )

    @app.get(
        "/workflows/{workflow_id}/versions",
        response_model=list[WorkflowVersionResponse],
    )
    def list_workflow_versions(
        workflow_id: str,
        current: Container = Depends(get_container),
    ) -> list[WorkflowVersionResponse]:

        versions = current.studio.list_workflow_versions(
            workflow_id
        )

        return [
            WorkflowVersionResponse(
                id=version.id,
                workflow_id=version.workflow_id,
                version=version.version,
                plan=json.loads(version.plan_json),
                created_at=version.created_at,
            )
            for version in versions
        ]

    @app.get(
        "/workflows/{workflow_id}/versions/{version}",
        response_model=WorkflowVersionResponse,
    )
    def get_workflow_version(
        workflow_id: str,
        version: str,
        current: Container = Depends(get_container),
    ) -> WorkflowVersionResponse:

        record = current.studio.get_workflow_version(
            workflow_id=workflow_id,
            version=version,
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Workflow version not found: "
                    f"{version}"
                ),
            )

        return WorkflowVersionResponse(
            id=record.id,
            workflow_id=record.workflow_id,
            version=record.version,
            plan=json.loads(record.plan_json),
            created_at=record.created_at,
        )

    @app.post(
        "/workflows/{workflow_id}/versions/{version}/activate",
        response_model=WorkflowResponse,
    )
    def activate_workflow_version(
        workflow_id: str,
        version: str,
        current: Container = Depends(get_container),
    ) -> WorkflowResponse:

        try:
            workflow = current.studio.activate_workflow_version(
                workflow_id,
                version,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        return WorkflowResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.name,
            active_version=workflow.active_version,
            status=workflow.status,
            created_at=workflow.created_at,
        )

    @app.post(
        "/workflows/{workflow_id}/execute",
        response_model=WorkflowExecutionResponse,
    )
    def execute_workflow(
        workflow_id: str,
        payload: WorkflowExecutionRequest,
        current: Container = Depends(get_container),
    ) -> WorkflowExecutionResponse:

        execution_id = str(uuid4())

        try:
            runtime = current.workflow_engine.execute(
                workflow_id=workflow_id,
                execution_id=execution_id,
                inputs=payload.inputs,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        return WorkflowExecutionResponse(
            execution_id=runtime.execution_id,
            workflow_id=runtime.workflow_id,
            workflow_version=runtime.workflow_version,
            status=runtime.status.value,
            success=runtime.success,
            outputs=runtime.outputs,
            error=runtime.error,
            started_at=runtime.started_at,
            finished_at=runtime.finished_at,
        )

    @app.get(
        "/workflow-executions/{execution_id}",
        response_model=WorkflowExecutionDetailResponse,
    )
    def workflow_execution_detail(
        execution_id: str,
        current: Container = Depends(get_container),
    ) -> WorkflowExecutionDetailResponse:
        try:
            data = (
                current.workflow_history
                .get_workflow_execution_detail(
                    execution_id
                )
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        return WorkflowExecutionDetailResponse(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            workflow_version=data["workflow_version"],
            status=data["status"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            error=data["error"],
            created_at=data["created_at"],
            started_at=data["started_at"],
            finished_at=data["finished_at"],
            traces=[
                CapabilityTraceResponse(
                    capability_id=trace.capability_id,
                    capability_version=trace.capability_version,
                    status=trace.status,
                    started_at=trace.started_at,
                    finished_at=trace.finished_at,
                )
                for trace in data["traces"]
            ],
        )
    
    instrument_fastapi(app)
    return app


async def _read_frame(file: UploadFile, container: Container):
    try:
        return container.uploads.read(file.filename, await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _validate_upload(file: UploadFile, category: str | None, container: Container, service: QualityService) -> ValidationResponse:
    content = await file.read()
    try:
        logger.info("validation_requested", extra={"event": "validation_requested", "upload_filename": file.filename, "requested_category": category})
        frame = container.uploads.read(file.filename, content)
        result = service.validate(frame, content, category)
        urls = {name: f"/executions/{result.execution_id}/reports/{name}" for name in result.report_paths}
        logger.info("validation_completed", extra={"event": "validation_completed", "execution_id": result.execution_id, "category": result.category, "cached": result.cached})
        return ValidationResponse(execution_id=result.execution_id, category=result.category, health_score=result.health_score, reports=urls, cached=result.cached)
    except ValidationRequestError as exc:
        logger.warning("validation_rejected", extra={"event": "validation_rejected", "upload_filename": file.filename, "reason": str(exc)})
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "validation_unexpected_error",
            extra={
                "event": "validation_unexpected_error",
                "upload_filename": file.filename,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise


def _preview(category: str, frame) -> TabularPreviewResponse:
    return TabularPreviewResponse(category=category, rows=len(frame), columns=[str(column) for column in frame.columns], records=frame.head(100).to_dict(orient="records"))


def _history_items(container: Container, limit: int) -> list[dict[str, str | float]]:
    return [{"id": item.id, "category": item.category, "health_score": item.health_score, "created_at": item.created_at.isoformat()} for item in container.executions.history(min(max(limit, 1), 100))]


def _download_report(container: Container, execution_id: str, report_format: str) -> FileResponse:
    if report_format not in {"excel", "html", "pdf", "json"}:
        raise HTTPException(status_code=404, detail="Unsupported report format")
    path = container.executions.report_path(execution_id, report_format)
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, filename=f"data-quality-report.{Path(path).suffix.lstrip('.')}")
def _execution_plan_from_payload(
    payload: dict,
):
    try:
        return ExecutionPlanSerializer.from_dict(
            payload
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid execution plan: {exc}",
        ) from exc
