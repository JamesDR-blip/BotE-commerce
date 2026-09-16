"""Composition root: dependency injection without mutable module globals."""
from __future__ import annotations

from agents.extraction import ExtractionAgent
from agents.intent_classifier import IntentClassifier
from agents.llm import LLMAssistantAgent
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
from application.audit.audit_service import AuditService
from application.approval.approval_service import ApprovalService
from application.changesets.changeset_service import ChangeSetService
from application.changesets.mutation_service import ChangeSetMutationService
from application.changesets.rollback_service import ChangeSetRollbackService
from application.changesets.query_service import ChangeSetQueryService
from application.datasets.artifact_materializer import DatasetArtifactMaterializer
from application.datasets.dataset_ingestion import DatasetIngestionService
from application.datasets.dataset_service import DatasetService
from application.lineage.lineage_tracking_service import LineageTrackingService
from application.memory.memory_service import AgentMemoryService
from application.quality.data_health_service import DataHealthService
from application.quality.quality_service import QualityService
from application.risk.risk_service import RiskService
from application.rules.rule_intelligence_service import RuleIntelligenceService
from application.workflows.authoring_service import WorkflowAuthoringService
from application.workflows.history_service import WorkflowHistoryService
from application.workflows.runtime_service import WorkflowRuntimeService
from application.workspace.project_service import WorkspaceProjectService
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
from capabilities.normalization import NormalizationCapability
from capabilities.qa import QACapability
from capabilities.validation import ValidationCapability
from configs.settings import Settings
from database.models import make_session_factory
from domain.catalog.mapping import MappingService
from domain.catalog.normalization import NormalizationService
from domain.capability_registry import CapabilityRegistry
from domain.capability_selector import CapabilitySelector
from domain.dependency_resolver import DependencyResolver
from domain.intent_resolver import IntentResolver
from domain.quality.anomalies import detect_anomalies
from domain.quality.health_score import HealthScoreService
from domain.studio.profiling import DatasetProfileService
from execution.capabilities.capability_execution_service import (
    CapabilityExecutionService,
)
from execution.capabilities.capability_executor import CapabilityExecutor
from execution.workflow.engine import WorkflowEngine, WorkflowExecutionWorker
from execution.shadow_execution_runner import ShadowExecutionRunner
from extractors.deterministic import DeterministicProductExtractor
from infrastructure.cache.ttl import TTLCache
from infrastructure.persistence.approval_repository import ApprovalRepository
from infrastructure.persistence.execution_trace import ExecutionTracePersistence
from infrastructure.persistence.risk_repository import RiskRepository
from infrastructure.persistence.risk_assessment_repository import RiskAssessmentRepository
from infrastructure.queue.workflow_execution_queue import (
    InProcessWorkflowExecutionQueue,
)
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from infrastructure.storage.dataset_storage import DatasetStorage
from infrastructure.upload.streaming_reader import StreamingTabularReader
from infrastructure.upload.tabular_reader import TabularUploadReader
from plugins.registry import ValidatorRegistry
from reports.generator import ReportAgent
from repositories.agent_memory import AgentMemoryRepository
from repositories.audit_events import AuditEventRepository
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)
from repositories.data_lineage_events import DataLineageEventRepository
from repositories.datasets import DatasetRepository
from repositories.changesets import ChangeSetRepository
from repositories.execution_traces import ExecutionTraceRepository
from repositories.executions import ExecutionRepository
from repositories.projects import ProjectRepository
from repositories.rules import RuleRepository
from repositories.users import UserRepository
from repositories.workflow_executions import WorkflowExecutionRepository
from repositories.workflows import WorkflowRepository
from repositories.workspaces import WorkspaceRepository
from services.authentication import AuthenticationService
from application.workflows.simulation_service import SimulationService
from application.autonomous.autonomous_ops_service import AutonomousOpsService
from application.autonomous.autonomous_operations_orchestrator import AutonomousOperationsOrchestrator
from domain.autonomous_operations import AutonomousPolicy
from services.authorization import AuthorizationService
from services.data_operations import DataOperationsService
from services.validation_service import ValidationService


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.authentication = AuthenticationService()
        self.authorization = AuthorizationService()

        sessions = make_session_factory(settings.database_url)
        self.sessions = sessions
        self.registry = ValidatorRegistry()
        self.rules = RuleRepository(settings.rules_path)

        self.risk_repository = RiskRepository(sessions)
        self.risk_assessment_repository = RiskAssessmentRepository(sessions)
        self.approval_repository = ApprovalRepository(sessions)

        self.risk_service = RiskService(
            policy=self.risk_repository.get_policy()
        )

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
            ExtractionAgent(
                DeterministicProductExtractor()
            ),
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

        normalization_capability = NormalizationCapability(
            self.normalization
        )
        self.capabilities.register(normalization_capability)

        cleaning_capability = CleaningCapability(
            self.data_operations
        )
        self.capabilities.register(cleaning_capability)

        extraction_capability = ExtractionCapability(
            self.agents.extraction
        )
        self.capabilities.register(extraction_capability)

        validation_capability = ValidationCapability(
            rules=self.agents.rules,
            validator=self.agents.validator,
            registry=self.registry,
        )
        self.capabilities.register(validation_capability)

        qa_capability = QACapability(
            self.agents.qa
        )
        self.capabilities.register(qa_capability)

        intent_classifier = IntentClassifier.from_registry(
            self.capabilities
        )
        intent_resolver = IntentResolver.from_registry(
            self.capabilities
        )

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

        intent_resolver = IntentResolver.from_registry(
            self.capabilities
        )

        self.planner = PlannerAgent(
            registry=self.capabilities,
            resolver=DependencyResolver(),
            intent_resolver=intent_resolver,
            selector=selector,
        )

        self.capability_executor = CapabilityExecutor(
            self.capabilities
        )

        self.workflow_capability_traces = CapabilityExecutionTraceRepository(
            sessions
        )
        self.workflow_trace_persistence = ExecutionTracePersistence(
            self.workflow_capability_traces
        )

        self.reports = ReportAgent(settings.reports_path)
        self.reporter = ReporterAgent(self.reports)
        self.executions = ExecutionRepository(sessions)
        self.execution_traces = ExecutionTraceRepository(
            sessions
        )

        self.execution_trace_persistence = ExecutionTracePersistence(
            self.execution_traces
        )
        self.workflow_executions = WorkflowExecutionRepository(sessions)
        self.users = UserRepository(sessions)
        self.workflows = WorkflowRepository(sessions)
        self.workspaces = WorkspaceRepository(sessions)
        self.projects = ProjectRepository(sessions)
        self.datasets = DatasetRepository(sessions)
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
            ingestion=self.dataset_ingestion,
        )
        self.workspace_projects = WorkspaceProjectService(
            workspaces=self.workspaces,
            projects=self.projects,
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
            audit_service=self.audit_service,
        )

        self.changeset_rollback_service = ChangeSetRollbackService(
            sessions=self.sessions,
            changesets=self.changesets,
            audit_service=self.audit_service,
        )
        self.changeset_query_service = ChangeSetQueryService(
            changesets=self.changesets,
        )

        self.workflow_history = WorkflowHistoryService(
            executions=self.workflow_executions,
            traces=self.workflow_capability_traces,
        )
        self.workflow_worker = WorkflowExecutionWorker(
            executions=self.workflow_executions,
            workflow_engine=self.workflow_engine,
        )
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
        )
        self.workflow_runtime = WorkflowRuntimeService(
            workflow_engine=lambda: self.workflow_engine,
            workflow_history=lambda: self.workflow_history,
            workflow_queue=lambda: self.workflow_queue,
            workflows=lambda: self.workflows,
            datasets=lambda: self.datasets,
            data_health=lambda: self.data_health,
            risk_service=lambda: self.risk_service,
            risk_assessments=lambda: self.risk_assessment_repository,
            workflow_executions=lambda: self.workflow_executions,
            changeset_service=lambda: self.changeset_service,
        )
        self.simulation_service = SimulationService(
            shadow_runner=self.shadow_execution_runner,
            workflows=self.workflows,
            datasets=self.datasets,
        )

        self.autonomous_ops = AutonomousOpsService(policy=AutonomousPolicy())
        self.autonomous_operations_orchestrator = (
            AutonomousOperationsOrchestrator(
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
                approval_service=self.approval_service,
                workflow_authoring=self.workflow_authoring,
                workflow_executions=self.workflow_executions,
                simulation_service=self.simulation_service,
                memory_service=self.agent_memory,
                audit_service=self.audit_service,
            )
        )


def build_container(
    app_settings: Settings | None = None,
) -> Container:

    if app_settings is None:
        app_settings = Settings()

    return Container(app_settings)
