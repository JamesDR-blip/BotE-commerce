"""FastAPI dependency providers backed by the application composition root."""
from domain.identity import CurrentUser
from application.workflows.simulation_service import SimulationService
from application.copilot.service import CopilotService

from fastapi import Depends, Header, HTTPException, Request

from services.authentication import AuthenticationService
from services.authorization import AuthorizationService
from services.data_operations import DataOperationsService
from application.datasets.dataset_service import DatasetService
from application.channels.canonical_product_service import CanonicalProductService
from application.channels.channel_sync_service import ChannelSyncService
from application.rules.rule_intelligence_service import RuleIntelligenceService
from domain.catalog.mapping import MappingService
from application.quality.quality_service import QualityService
from application.quality.data_health_service import DataHealthService
from application.workspace.project_service import WorkspaceProjectService
from infrastructure.upload.tabular_reader import TabularUploadReader
from application.workflows.authoring_service import WorkflowAuthoringService
from application.workflows.history_service import WorkflowHistoryService
from application.workflows.runtime_service import WorkflowRuntimeService
from application.changesets.query_service import ChangeSetQueryService
from application.lineage.lineage_tracking_service import LineageTrackingService
from application.audit.audit_service import AuditService

from repositories.channels import ChannelRepository
from repositories.executions import ExecutionRepository
from repositories.execution_traces import ExecutionTraceRepository
from repositories.sync_jobs import SyncJobRepository


def get_quality_service(request: Request) -> QualityService:
    return request.app.state.quality_service


def get_data_health_service(request: Request) -> DataHealthService:
    return request.app.state.data_health


def get_data_operations(request: Request) -> DataOperationsService:
    return request.app.state.data_operations


def get_mapping_service(request: Request) -> MappingService:
    return request.app.state.mapping_service


def get_workflow_history(request: Request) -> WorkflowHistoryService:
    return request.app.state.workflow_history


def get_workflow_authoring_service(request: Request) -> WorkflowAuthoringService:
    return request.app.state.workflow_authoring


def get_dataset_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


def get_canonical_product_service(
    request: Request,
) -> CanonicalProductService:
    return request.app.state.container.canonical_product_service


def get_channel_repository(request: Request) -> ChannelRepository:
    return request.app.state.container.channels


def get_channel_sync_service(request: Request) -> ChannelSyncService:
    return request.app.state.container.channel_sync


def get_sync_job_repository(request: Request) -> SyncJobRepository:
    return request.app.state.container.sync_jobs


def get_workspace_project_service(
    request: Request,
) -> WorkspaceProjectService:
    return request.app.state.workspace_projects


def get_workflow_runtime(request: Request) -> WorkflowRuntimeService:
    return request.app.state.workflow_runtime


def get_simulation_service(request: Request) -> SimulationService:
    return request.app.state.simulation_service


def get_approval_service(request: Request):
    return request.app.state.container.approval_service


def get_execution_repository(request: Request) -> ExecutionRepository:
    return request.app.state.execution_repository


def get_execution_trace_repository(
    request: Request,
) -> ExecutionTraceRepository:
    return request.app.state.execution_trace_repository


def get_upload_reader(request: Request) -> TabularUploadReader:
    return request.app.state.upload_reader


def get_categories(request: Request) -> list[str]:
    return request.app.state.categories


def get_authentication_service(
    request: Request,
) -> AuthenticationService:
    return request.app.state.authentication


def get_current_user(
    authorization: str | None = Header(default=None),
    authentication: AuthenticationService = Depends(
        get_authentication_service
    ),
) -> CurrentUser:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )

    return authentication.authenticate(token)


def get_authorization_service(
    request: Request,
) -> AuthorizationService:
    return request.app.state.authorization


def get_rule_intelligence_service(
    request: Request,
) -> RuleIntelligenceService:
    return request.app.state.rule_intelligence


def get_changeset_query_service(
    request: Request,
) -> ChangeSetQueryService:
    return request.app.state.container.changeset_query_service


def get_changeset_rollback_service(request: Request):
    return request.app.state.container.changeset_rollback_service


def get_lineage_tracking_service(
    request: Request,
) -> LineageTrackingService:
    return request.app.state.container.lineage_tracking


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.container.audit_service


def get_copilot_service(request: Request) -> CopilotService:
    return request.app.state.copilot


def get_marketplace_service(request: Request):
    return request.app.state.container.marketplace
