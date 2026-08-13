"""Composition root: dependency injection without mutable module globals."""
from __future__ import annotations
from configs import settings
from configs.settings import Settings
from database.models import make_session_factory

from repositories.executions import ExecutionRepository
from repositories.users import UserRepository
from repositories.rules import RuleRepository

from services.cache import TTLCache
from services.upload_reader import TabularUploadReader
from services.health_score_service import HealthScoreService
from services.validation_service import ValidationService
from services.data_operations import DataOperationsService
from services.mapping_service import MappingService
from services.capability_executor import CapabilityExecutor
from services.capability_execution_service import CapabilityExecutionService
from services.quality_service import QualityService

from plugins.registry import ValidatorRegistry

from agents.workflow import Agents, AutoFixAgent, ClassifierAgent, QAAgent, RuleRetrieverAgent, ValidatorAgent
from agents.requirement import RequirementAgent
from agents.reporter import ReporterAgent
from agents.extraction import ExtractionAgent
from agents.planner import PlannerAgent
from extractors.deterministic import DeterministicProductExtractor
from agents.graph import WorkflowBuilder
from agents.llm import LLMAssistantAgent

from reports.generator import ReportAgent

from domain.capability_registry import CapabilityRegistry
from domain.dependency_resolver import DependencyResolver

from capabilities.validation import ValidationCapability
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability

class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        sessions = make_session_factory(settings.database_url)
        self.registry = ValidatorRegistry()
        self.rules = RuleRepository(settings.rules_path)
        self.validation = ValidationService()
        self.health_scores = HealthScoreService()
        self.agents = Agents(RequirementAgent(), ClassifierAgent(), RuleRetrieverAgent(self.rules), ExtractionAgent(DeterministicProductExtractor()), AutoFixAgent(), ValidatorAgent(self.validation), QAAgent(self.health_scores))

        self.capabilities = CapabilityRegistry()

        self.data_operations = DataOperationsService(
            self.agents,
            self.registry,
        )

        cleaning_capability = CleaningCapability(
            self.data_operations
        )
        self.capabilities.register(cleaning_capability)

        extraction_capability = ExtractionCapability(
            self.agents.extraction
        )
        self.capabilities.register(extraction_capability)

        validation_capability = ValidationCapability(
            lambda: self.workflow
        )
        self.capabilities.register(validation_capability)

        self.planner = PlannerAgent(
            catalog=self.capabilities.catalog(),
            resolver=DependencyResolver(),
        )

        self.workflow = WorkflowBuilder(
            self.agents,
            self.registry,
            planner=self.planner,
        )


        self.capability_executor = CapabilityExecutor(
            self.capabilities
        )
        
        self.capability_execution = CapabilityExecutionService(
            planner=self.planner,
            executor=self.capability_executor,
        )
        
        self.reports = ReportAgent(settings.reports_path)
        self.reporter = ReporterAgent(self.reports)
        self.executions = ExecutionRepository(sessions)
        self.users = UserRepository(sessions)
        self.cache = TTLCache(settings.cache_ttl_seconds)
        self.uploads = TabularUploadReader(settings.max_upload_bytes)
        self.mapping = MappingService()

        self.quality_service = QualityService(
            requirements=self.agents.requirements,
            capability_execution=self.capability_execution,
            executions=self.executions,
            cache=self.cache,
            reporter=self.reporter,
            enable_llm=settings.enable_llm,
        )
