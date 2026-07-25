"""Composition root: dependency injection without mutable module globals."""
from __future__ import annotations
from configs.settings import Settings
from models.database import make_session_factory
from repositories.executions import ExecutionRepository
from repositories.rules import RuleRepository
from services.cache import TTLCache
from services.plugins import ValidatorRegistry
from agents.workflow import Agents, AutoFixAgent, ClassifierAgent, QAAgent, RuleRetrieverAgent, ValidatorAgent
from agents.llm import LLMAssistantAgent
from reports.generator import ReportAgent


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        sessions = make_session_factory(settings.database_url)
        self.registry = ValidatorRegistry()
        self.rules = RuleRepository(settings.rules_path)
        self.agents = Agents(ClassifierAgent(), RuleRetrieverAgent(self.rules), AutoFixAgent(), ValidatorAgent(), QAAgent())
        self.llm = LLMAssistantAgent(settings.enable_llm, settings.google_api_key, settings.llm_model)
        self.reports = ReportAgent(settings.reports_path)
        self.executions = ExecutionRepository(sessions)
        self.cache = TTLCache(settings.cache_ttl_seconds)
