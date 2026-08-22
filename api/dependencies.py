"""FastAPI dependency providers backed by the application composition root."""
from fastapi import Request

from services.container import Container
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService
from services.quality_service import QualityService
from services.workflow_history_service import WorkflowHistoryService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_quality_service(request: Request) -> QualityService:
    return request.app.state.quality_service


def get_data_operations(request: Request) -> DataOperationsService:
    return request.app.state.data_operations


def get_mapping_service(request: Request) -> MappingService:
    return request.app.state.mapping_service

def get_workflow_history(request: Request) -> WorkflowHistoryService:
    return request.app.state.container.workflow_history

def get_workflow_engine(request: Request):
    return request.app.state.container.workflow_engine