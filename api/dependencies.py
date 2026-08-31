"""FastAPI dependency providers backed by the application composition root."""
from fastapi import Request

from services.data_operations import DataOperationsService
from repositories.executions import ExecutionRepository
from services.mapping_service import MappingService
from services.quality_service import QualityService
from services.studio_service import StudioService
from services.upload_reader import TabularUploadReader
from services.workflow_history_service import WorkflowHistoryService
from services.workflow_runtime_service import WorkflowRuntimeService

from repositories.execution_traces import ExecutionTraceRepository


def get_quality_service(request: Request) -> QualityService:
    return request.app.state.quality_service


def get_data_operations(request: Request) -> DataOperationsService:
    return request.app.state.data_operations


def get_mapping_service(request: Request) -> MappingService:
    return request.app.state.mapping_service

def get_workflow_history(
    request: Request,
) -> WorkflowHistoryService:
    return request.app.state.workflow_history

def get_studio_service(
    request: Request,
) -> StudioService:
    return request.app.state.studio_service

def get_workflow_runtime(
    request: Request,
) -> WorkflowRuntimeService:
    return request.app.state.workflow_runtime


def get_execution_repository(
    request: Request,
) -> ExecutionRepository:
    return request.app.state.execution_repository


def get_execution_trace_repository(
    request: Request,
) -> ExecutionTraceRepository:
    return request.app.state.execution_trace_repository


def get_upload_reader(
    request: Request,
) -> TabularUploadReader:
    return request.app.state.upload_reader


def get_categories(
    request: Request,
) -> list[str]:
    return request.app.state.categories