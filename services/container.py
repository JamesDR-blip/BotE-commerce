"""Composition root: dependency injection without mutable module globals."""

from __future__ import annotations

from agents.extraction import ExtractionAgent
from agents.intent_classifier import IntentClassifier
from agents.parameter_resolver import ParameterResolver
from agents.planner import PlannerAgent
from agents.reporter import ReporterAgent
from agents.requirement import RequirementAgent
from agents.workflow import (
    Agents,
    AutoFixAgent,
    ClassifierAgent,
    QAAgent,
    RuleRetrieverAgent,
    ValidatorAgent,
)
from application.approval.approval_changeset_service import ApprovalChangeSetService
from application.approval.approval_service import ApprovalService
from application.audit.audit_service import AuditService
from application.autonomous.autonomous_operations_orchestrator import (
    AutonomousOperationsOrchestrator,
)
from application.autonomous.autonomous_ops_service import AutonomousOpsService
from application.changesets.changeset_service import ChangeSetService
from application.changesets.mutation_service import ChangeSetMutationService
from application.changesets.query_service import ChangeSetQueryService
from application.changesets.rollback_service import ChangeSetRollbackService
from application.channels.canonical_product_service import CanonicalProductService
from application.channels.channel_sync_service import ChannelSyncService
from application.copilot.agent import CopilotAgent
from application.copilot.application_tools import (
    CopilotToolServices,
    build_copilot_tools,
)
from application.copilot.service import CopilotService
from application.datasets.artifact_materializer import DatasetArtifactMaterializer
from application.datasets.dataset_ingestion import DatasetIngestionService
from application.datasets.dataset_service import DatasetService
from application.lineage.lineage_tracking_service import LineageTrackingService
from application.marketplace.marketplace_service import MarketplaceService
from application.memory.memory_service import AgentMemoryService
from application.quality.data_health_service import DataHealthService
from application.quality.quality_service import QualityService
from application.risk.risk_service import RiskService
from application.rules.rule_intelligence_service import RuleIntelligenceService
from application.workflows.authoring_service import WorkflowAuthoringService
from application.workflows.history_service import WorkflowHistoryService
from application.workflows.runtime_service import WorkflowRuntimeService
from application.workflows.simulation_service import SimulationService
from application.workspace.project_service import WorkspaceProjectService
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
from capabilities.normalization import NormalizationCapability
from capabilities.qa import QACapability
from capabilities.validation import ValidationCapability
from configs.settings import Settings
from database.models import make_session_factory
from domain.autonomous_operations import AutonomousPolicy
from domain.capability_registry import CapabilityRegistry
from domain.capability_selector import CapabilitySelector
from domain.catalog.mapping import MappingService
from domain.catalog.normalization import NormalizationService
from domain.dependency_resolver import DependencyResolver
from domain.intent_resolver import IntentResolver
from domain.quality.anomalies import detect_anomalies
from domain.quality.health_score import HealthScoreService
from domain.studio.profiling import DatasetProfileService
from execution.capabilities.capability_execution_service import (
    CapabilityExecutionService,
)
from execution.capabilities.capability_executor import CapabilityExecutor
from execution.shadow_execution_runner import ShadowExecutionRunner
from execution.workflow.engine import WorkflowEngine, WorkflowExecutionWorker
from extractors.deterministic import DeterministicProductExtractor
from infrastructure.cache.ttl import TTLCache
from infrastructure.channels.connector_factory import ChannelConnectorFactory
from infrastructure.channels.http_client import HttpClient
from infrastructure.marketplace.catalog import MarketplacePackageCatalog
from infrastructure.marketplace.installer import PackageInstaller
from infrastructure.marketplace.rule_pack import MarketplaceRulePackLoader
from infrastructure.persistence.approval_repository import ApprovalRepository
from infrastructure.persistence.agent_memory_repository import (
    AgentMemoryRepository,
)
from infrastructure.persistence.execution_trace import ExecutionTracePersistence
from infrastructure.persistence.risk_assessment_repository import (
    RiskAssessmentRepository,
)
from infrastructure.persistence.risk_repository import RiskRepository
from infrastructure.queue.redis_workflow_execution_queue import (
    RedisWorkflowExecutionQueue,
)
from infrastructure.queue.workflow_execution_queue import (
    InProcessWorkflowExecutionQueue,
)
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from infrastructure.security.credential_cipher import FernetCredentialCipher
from infrastructure.security.unavailable_credential_cipher import (
    UnavailableCredentialCipher,
)
from infrastructure.storage.dataset_storage import DatasetStorage
from infrastructure.upload.streaming_reader import StreamingTabularReader
from infrastructure.upload.tabular_reader import TabularUploadReader
from plugins.registry import ValidatorRegistry
from reports.generator import ReportAgent
from repositories.audit_events import AuditEventRepository
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)
from repositories.changesets import ChangeSetRepository
from repositories.channel_mappings import ChannelMappingRepository
from repositories.channels import ChannelRepository
from repositories.compliance_policies import CompliancePolicyRepository
from repositories.data_lineage_events import DataLineageEventRepository
from repositories.datasets import DatasetRepository
from repositories.execution_traces import ExecutionTraceRepository
from repositories.executions import ExecutionRepository
from repositories.organizations import OrganizationRepository
from repositories.projects import ProjectRepository
from repositories.quotas import QuotaRepository
from repositories.rbac import RBACRepository
from repositories.rules import RuleRepository
from repositories.sync_jobs import SyncAttemptRepository, SyncJobRepository
from repositories.users import UserRepository
from repositories.workflow_executions import WorkflowExecutionRepository
from repositories.workflows import WorkflowRepository
from repositories.workspaces import WorkspaceRepository
from services.authentication import AuthenticationService
from services.authorization import AuthorizationService
from services.compliance import ComplianceService
from services.data_operations import DataOperationsService
from services.quota import QuotaService
from services.validation_service import ValidationService


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.authentication = AuthenticationService()

        sessions = make_session_factory(
            settings.database_url,
            create_schema=settings.environment != "production",
            require_current_revision=settings.environment == "production",
        )
        self.sessions = sessions

        self.rbac = RBACRepository(sessions)
        self.quotas = QuotaRepository(sessions)
        self.compliance_policies = CompliancePolicyRepository(sessions)
        self.quota_service = QuotaService(
            quotas=self.quotas,
        )
        self.compliance_service = ComplianceService(
            policies=self.compliance_policies,
        )
        self.authorization = AuthorizationService(
            rbac_repository=self.rbac,
        )

        self.registry = ValidatorRegistry()
        self.rules = RuleRepository(settings.rules_path)

        self.risk_repository = RiskRepository(sessions)
        self.risk_assessment_repository = RiskAssessmentRepository(sessions)
        self.approval_repository = ApprovalRepository(sessions)

        self.risk_service = RiskService(policy=self.risk_repository.get_policy())

        self.rule_retriever = ChromaRuleRetriever(
            path=settings.rule_index_path,
        )
        self.rule_intelligence = RuleIntelligenceService(
            retriever=self.rule_retriever,
        )
        self.validation = ValidationService()
        self.health_scores = HealthScoreService()
        self.agents = Agents(
            RequirementAgent(),
            ClassifierAgent(),
            RuleRetrieverAgent(self.rules, self.rule_retriever),
            ExtractionAgent(DeterministicProductExtractor()),
            AutoFixAgent(),
            ValidatorAgent(self.validation),
            QAAgent(
                anomaly_detector=detect_anomalies,
                health_scores=self.health_scores,
            ),
        )
        self.capabilities = CapabilityRegistry()

        self.data_operations = DataOperationsService(
            self.agents,
            self.registry,
        )
        self.normalization = NormalizationService()

        normalization_capability = NormalizationCapability(self.normalization)
        self.capabilities.register(normalization_capability)

        cleaning_capability = CleaningCapability(self.data_operations)
        self.capabilities.register(cleaning_capability)

        extraction_capability = ExtractionCapability(self.agents.extraction)
        self.capabilities.register(extraction_capability)

        validation_capability = ValidationCapability(
            rules=self.agents.rules,
            validator=self.agents.validator,
            registry=self.registry,
        )
        self.capabilities.register(validation_capability)

        qa_capability = QACapability(self.agents.qa)
        self.capabilities.register(qa_capability)

        intent_classifier = IntentClassifier.from_registry(self.capabilities)
        intent_resolver = IntentResolver.from_registry(self.capabilities)

        self.memories = AgentMemoryRepository(sessions)
        self.agent_memory = AgentMemoryService(memories=self.memories)

        parameter_resolver = ParameterResolver(
            memory_service=self.agent_memory,
        )

        self.agents.requirements = RequirementAgent(
            classifier=intent_classifier,
            intent_resolver=intent_resolver,
            parameter_resolver=parameter_resolver,
            catalog=self.capabilities.catalog(),
        )

        selector = CapabilitySelector(
            available_capabilities=lambda: self.capabilities.catalog().keys(),
        )

        intent_resolver = IntentResolver.from_registry(self.capabilities)

        self.planner = PlannerAgent(
            registry=self.capabilities,
            resolver=DependencyResolver(),
            intent_resolver=intent_resolver,
            selector=selector,
        )

        self.capability_executor = CapabilityExecutor(self.capabilities)

        self.workflow_capability_traces = CapabilityExecutionTraceRepository(sessions)
        self.workflow_trace_persistence = ExecutionTracePersistence(
            self.workflow_capability_traces
        )

        self.reports = ReportAgent(settings.reports_path)
        self.reporter = ReporterAgent(self.reports)
        self.executions = ExecutionRepository(sessions)
        self.execution_traces = ExecutionTraceRepository(sessions)

        self.execution_trace_persistence = ExecutionTracePersistence(
            self.execution_traces
        )
        self.workflow_executions = WorkflowExecutionRepository(sessions)
        self.users = UserRepository(sessions)
        self.organizations = OrganizationRepository(sessions)
        self.workflows = WorkflowRepository(sessions)
        self.workspaces = WorkspaceRepository(sessions)
        self.projects = ProjectRepository(sessions)
        self.datasets = DatasetRepository(sessions)
        self.channels = (
            ChannelRepository(
                sessions,
                credential_cipher=(
                    FernetCredentialCipher(
                        settings.channel_credentials_encryption_key.get_secret_value()
                    )
                    if settings.channel_credentials_encryption_key is not None
                    else UnavailableCredentialCipher()
                ),
            ),
        )
        self.channel_mappings = ChannelMappingRepository(sessions)
        self.sync_jobs = SyncJobRepository(sessions)
        self.sync_attempts = SyncAttemptRepository(sessions)
        self.changesets = ChangeSetRepository(sessions)
        self.data_lineage_events = DataLineageEventRepository(sessions)
        self.audit_events = AuditEventRepository(sessions)
        self.lineage_tracking = LineageTrackingService(
            repository=self.data_lineage_events,
        )
        self.capability_execution = CapabilityExecutionService(
            executor=self.capability_executor,
            lineage_tracking=self.lineage_tracking,
        )
        self.audit_service = AuditService(
            sessions=self.sessions,
            repository=self.audit_events,
        )
        self.cache = TTLCache(settings.cache_ttl_seconds)
        self.uploads = TabularUploadReader(settings.max_upload_bytes)
        self.streaming_uploads = StreamingTabularReader(
            settings.max_upload_bytes,
        )
        self.dataset_storage = DatasetStorage(settings.dataset_storage_path)

        self.marketplace_catalog = MarketplacePackageCatalog(
            root=settings.marketplace_staging_path,
        )
        self.marketplace_installer = PackageInstaller(
            staging_root=settings.marketplace_staging_path,
        )
        self.marketplace_rule_pack_loader = MarketplaceRulePackLoader()
        self.marketplace = MarketplaceService(
            installer=self.marketplace_installer,
            catalog=self.marketplace_catalog,
            rule_pack_loader=self.marketplace_rule_pack_loader,
        )

        self.channel_http_client = HttpClient()
        self.channel_connector_factory = ChannelConnectorFactory(
            http_client=self.channel_http_client,
        )

        self.shadow_execution_runner = ShadowExecutionRunner(
            capability_execution=self.capability_execution,
            dataset_storage=self.dataset_storage,
            streaming_reader=self.streaming_uploads,
        )
        self.dataset_profile = DatasetProfileService()
        self.dataset_ingestion = DatasetIngestionService(
            reader=self.uploads,
            streaming_reader=self.streaming_uploads,
            datasets=self.datasets,
            profiler=self.dataset_profile,
            storage=self.dataset_storage,
        )
        self.mapping = MappingService()
        self.canonical_product_service = CanonicalProductService(
            datasets=self.datasets,
            storage=self.dataset_storage,
            reader=self.uploads,
            mapping=self.mapping,
            normalization=self.normalization,
        )

        self.channel_sync = ChannelSyncService(
            channels=self.channels,
            mappings=self.channel_mappings,
            sync_jobs=self.sync_jobs,
            sync_attempts=self.sync_attempts,
            canonical_products=self.canonical_product_service,
            datasets=self.datasets,
            projects=self.projects,
            connector_factory=(
                lambda channel, credentials: self.channel_connector_factory.create(
                    channel=channel,
                    credentials=credentials,
                )
            ),
            audit_service=self.audit_service,
        )

        self.data_health = DataHealthService(
            datasets=self.datasets,
            executions=self.executions,
        )
        self.quality_service = QualityService(
            requirements=self.agents.requirements,
            planner=self.planner,
            capability_execution=self.capability_execution,
            executions=self.executions,
            trace_persistence=self.execution_trace_persistence,
            cache=self.cache,
            reporter=self.reporter,
            enable_llm=settings.enable_llm,
        )
        self.workflow_authoring = WorkflowAuthoringService(
            workflows=self.workflows,
            projects=self.projects,
        )
        self.dataset_service = DatasetService(
            datasets=self.datasets,
            projects=self.projects,
            workspaces=self.workspaces,
            ingestion=self.dataset_ingestion,
            authorization=self.authorization,
            quota_service=self.quota_service,
            compliance_service=self.compliance_service,
        )
        self.workspace_projects = WorkspaceProjectService(
            workspaces=self.workspaces,
            projects=self.projects,
            authorization=self.authorization,
        )
        self.workflow_engine = WorkflowEngine(
            workflows=self.workflows,
            capability_execution=self.capability_execution,
            executions=self.workflow_executions,
            trace_persistence=self.workflow_trace_persistence,
            datasets=self.datasets,
            streaming_reader=self.streaming_uploads,
            dataset_storage=self.dataset_storage,
        )
        self.dataset_artifact_materializer = DatasetArtifactMaterializer(
            storage=self.dataset_storage,
        )
        self.changeset_service = ChangeSetService(
            workflows=self.workflows,
            executions=self.workflow_executions,
            datasets=self.datasets,
            dataset_storage=self.dataset_storage,
            capability_execution=self.capability_execution,
            artifact_materializer=self.dataset_artifact_materializer,
            changesets=self.changesets,
        )
        self.changeset_mutation_service = ChangeSetMutationService(
            sessions=self.sessions,
            changesets=self.changesets,
            dataset_storage=self.dataset_storage,
            audit_service=self.audit_service,
            compliance_service=self.compliance_service,
        )

        self.changeset_rollback_service = ChangeSetRollbackService(
            sessions=self.sessions,
            changesets=self.changesets,
            dataset_storage=self.dataset_storage,
            audit_service=self.audit_service,
        )
        self.changeset_query_service = ChangeSetQueryService(
            changesets=self.changesets,
        )

        self.workflow_history = WorkflowHistoryService(
            executions=self.workflow_executions,
            traces=self.workflow_capability_traces,
            workflows=self.workflows,
            projects=self.projects,
            workspaces=self.workspaces,
            authorization=self.authorization,
        )
        self.workflow_worker = WorkflowExecutionWorker(
            executions=self.workflow_executions,
            workflow_engine=self.workflow_engine,
        )
        if self.settings.workflow_queue_backend == "redis":
            if not self.settings.redis_url:
                raise ValueError(
                    "redis_url is required when the workflow queue backend is Redis"
                )
            self.workflow_queue = RedisWorkflowExecutionQueue(
                redis_url=self.settings.redis_url,
                stream_name=self.settings.redis_stream_name,
            )
        else:
            self.workflow_queue = InProcessWorkflowExecutionQueue(
                worker=self.workflow_worker.run,
            )
        self.approval_changeset_service = ApprovalChangeSetService(
            sessions=self.sessions,
            approvals=self.approval_repository,
            changesets=self.changesets,
            workflow_executions=self.workflow_executions,
            audit_service=self.audit_service,
        )
        self.approval_service = ApprovalService(
            self.approval_repository,
            workflow_executions=self.workflow_executions,
            workflow_queue=self.workflow_queue,
            approval_changeset_service=self.approval_changeset_service,
            workflows=self.workflows,
            projects=self.projects,
            workspaces=self.workspaces,
            authorization=self.authorization,
        )
        self.workflow_runtime = WorkflowRuntimeService(
            workflow_engine=lambda: self.workflow_engine,
            workflow_history=lambda: self.workflow_history,
            workflow_queue=lambda: self.workflow_queue,
            workflows=lambda: self.workflows,
            datasets=lambda: self.datasets,
            projects=lambda: self.projects,
            workspaces=lambda: self.workspaces,
            authorization=lambda: self.authorization,
            data_health=lambda: self.data_health,
            risk_service=lambda: self.risk_service,
            risk_assessments=lambda: self.risk_assessment_repository,
            workflow_executions=lambda: self.workflow_executions,
            changeset_service=lambda: self.changeset_service,
            approval_service=lambda: self.approval_service,
            quota_service=lambda: self.quota_service,
            compliance_service=lambda: self.compliance_service,
        )
        self.simulation_service = SimulationService(
            shadow_runner=self.shadow_execution_runner,
            workflows=self.workflows,
            datasets=self.datasets,
        )

        copilot_service_ref: dict[str, CopilotService] = {}

        def author_workflow_handler(
            *,
            current_user,
            arguments,
        ):
            service = copilot_service_ref.get("service")
            if service is None:
                raise RuntimeError("CopilotService is not initialized")
            return service.author_workflow(
                current_user=current_user,
                project_id=arguments.project_id,
                name=arguments.name,
                user_request=arguments.user_request,
            )

        self.copilot_tools = build_copilot_tools(
            services=CopilotToolServices(
                dataset_service=self.dataset_service,
                data_health=self.data_health,
                simulation_service=self.simulation_service,
                workflow_runtime=self.workflow_runtime,
                approval_service=self.approval_service,
            ),
            author_workflow_handler=author_workflow_handler,
        )

        self.copilot_agent = None
        if settings.enable_llm and settings.google_api_key:
            from google import genai

            client = genai.Client(api_key=settings.google_api_key)
            self.copilot_agent = CopilotAgent(
                model=client.models,
                model_name=settings.llm_model,
                tool_registry=self.copilot_tools,
            )

        self.copilot = CopilotService(
            requirements=self.agents.requirements,
            planner=self.planner,
            projects=self.projects,
            tools=self.copilot_tools,
            agent=self.copilot_agent,
        )
        copilot_service_ref["service"] = self.copilot

        self.autonomous_ops = AutonomousOpsService(policy=AutonomousPolicy())
        self.autonomous_operations_orchestrator = AutonomousOperationsOrchestrator(
            data_health=self.data_health,
            requirements=self.agents.requirements,
            planner=self.planner,
            risk_service=self.risk_service,
            autonomous_ops=self.autonomous_ops,
            changeset_service=self.changeset_service,
            changeset_mutation=self.changeset_mutation_service,
            changeset_rollback=self.changeset_rollback_service,
            changesets=self.changesets,
            datasets=self.datasets,
            workflow_authoring=self.workflow_authoring,
            workflow_executions=self.workflow_executions,
            simulation_service=self.simulation_service,
            memory_service=self.agent_memory,
            audit_service=self.audit_service,
            approval_service=self.approval_service,
        )


def build_container(
    app_settings: Settings | None = None,
) -> Container:

    if app_settings is None:
        app_settings = Settings()

    return Container(app_settings)
