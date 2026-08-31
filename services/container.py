"""Composition root: dependency injection without mutable module globals."""
from __future__ import annotations
from database.models import make_session_factory
from extractors.deterministic import DeterministicProductExtractor
from plugins.registry import ValidatorRegistry
from reports.generator import ReportAgent
from configs.settings import Settings

from repositories.executions import ExecutionRepository
from repositories.users import UserRepository
from repositories.rules import RuleRepository
from repositories.workspaces import WorkspaceRepository
from repositories.projects import ProjectRepository
from repositories.datasets import DatasetRepository
from repositories.workflows import WorkflowRepository
from repositories.workflow_executions import WorkflowExecutionRepository
from repositories.execution_traces import ExecutionTraceRepository
from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)

from domain.capability_selector import CapabilitySelector
from domain.capability_registry import CapabilityRegistry
from domain.dependency_resolver import DependencyResolver
from domain.intent_resolver import IntentResolver

from capabilities.validation import ValidationCapability
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
from capabilities.normalization import NormalizationCapability
from capabilities.qa import QACapability

from agents.workflow import Agents, AutoFixAgent, ClassifierAgent, QAAgent, RuleRetrieverAgent, ValidatorAgent
from agents.requirement import RequirementAgent
from agents.reporter import ReporterAgent
from agents.extraction import ExtractionAgent
from agents.parameter_resolver import ParameterResolver
from agents.planner import PlannerAgent
from agents.llm import LLMAssistantAgent
from agents.intent_classifier import IntentClassifier

from services.cache import TTLCache
from services.upload_reader import TabularUploadReader
from services.health_score_service import HealthScoreService
from services.validation_service import ValidationService
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService
from services.capability_executor import CapabilityExecutor
from services.capability_execution_service import CapabilityExecutionService
from services.dataset_ingestion import DatasetIngestionService
from services.dataset_profile import DatasetProfileService
from services.quality_service import QualityService
from services.normalization_service import NormalizationService
from services.studio_service import StudioService
from services.workflow_engine import WorkflowEngine
from services.execution_trace_persistence import (
    ExecutionTracePersistence,
)
from services.workflow_history_service import (
    WorkflowHistoryService,
)
from services.workflow_runtime_service import WorkflowRuntimeService
class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        sessions = make_session_factory(settings.database_url)
        self.registry = ValidatorRegistry()
        self.rules = RuleRepository(settings.rules_path)
        self.validation = ValidationService()
        self.health_scores = HealthScoreService()
        self.agents = Agents(
            RequirementAgent(),
            ClassifierAgent(),
            RuleRetrieverAgent(self.rules),
            ExtractionAgent(
                DeterministicProductExtractor()
            ),
            AutoFixAgent(),
            ValidatorAgent(self.validation),
            QAAgent(self.health_scores),
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

        parameter_resolver = ParameterResolver()

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
        self.capability_execution = CapabilityExecutionService(
            planner=self.planner,
            executor=self.capability_executor,
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
        self.cache = TTLCache(settings.cache_ttl_seconds)
        self.uploads = TabularUploadReader(settings.max_upload_bytes)
        self.dataset_profile = DatasetProfileService()
        self.dataset_ingestion = DatasetIngestionService(
            reader=self.uploads,
            datasets=self.datasets,
            profiler=self.dataset_profile,
        )
        self.mapping = MappingService()

        self.quality_service = QualityService(
            requirements=self.agents.requirements,
            capability_execution=self.capability_execution,
            executions=self.executions,
            trace_persistence=self.execution_trace_persistence,
            cache=self.cache,
            reporter=self.reporter,
            enable_llm=settings.enable_llm,
        )
        self.studio = StudioService(
            workspaces=self.workspaces,
            projects=self.projects,
            datasets=self.datasets,
            workflows=self.workflows,
            ingestion=self.dataset_ingestion,
        )
        self.workflow_engine = WorkflowEngine(
            workflows=self.workflows,
            capability_execution=self.capability_execution,
            executions=self.workflow_executions,
            trace_persistence=self.workflow_trace_persistence,
        )
        self.workflow_history = (
                    WorkflowHistoryService(
                        executions=self.workflow_executions,
                        traces=self.workflow_capability_traces,
                    )
                )
        self.workflow_runtime = WorkflowRuntimeService(
            workflow_engine=lambda: self.workflow_engine,
            workflow_history=lambda: self.workflow_history,
        )
def build_container(
    app_settings: Settings | None = None,
) -> Container:

    if app_settings is None:
        app_settings = Settings()

    return Container(app_settings)
