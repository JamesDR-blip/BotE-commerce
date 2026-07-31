from pathlib import Path

import pandas as pd

from agents.category import CategoryAgent
from agents.llm import LLMAssistantAgent
from agents.qa import QAAgent
from agents.requirement import RequirementAgent, ValidationRequirement
from agents.rule_retriever import RuleRetrieverAgent
from domain.models import ValidationIssue, ValidationResult
from agents.reporter import ReporterAgent
from repositories.rules import RuleRepository


def test_requirement_and_category_agents_produce_typed_intent() -> None:
    requirement = RequirementAgent().interpret("Fashion")
    assert requirement == ValidationRequirement(requested_category="Fashion")
    assert CategoryAgent().classify(pd.DataFrame({"Size": ["M"]}), ["Fashion", "Cosmetics"], requirement.requested_category) == "Fashion"


def test_rule_retriever_and_qa_keep_existing_contracts() -> None:
    rules, version = RuleRetrieverAgent(RuleRepository(Path("rules_library.yaml"))).retrieve("Fashion")
    result = QAAgent().result(pd.DataFrame({"Size": ["M"]}), [ValidationIssue(2, "Color", "missing", "Missing")], "Fashion", version)
    assert rules.category == "Fashion"
    assert result.quarantine.shape[0] == 1


def test_reporter_delegates_to_existing_report_generator() -> None:
    class StubReportGenerator:
        def generate(self, execution_id: str, result: ValidationResult) -> dict[str, str]:
            assert execution_id == "execution"
            assert result.category == "Fashion"
            return {"json": "report.json"}

    result = ValidationResult("Fashion", pd.DataFrame(), pd.DataFrame(), [], 100.0, "1")
    paths = ReporterAgent(StubReportGenerator()).generate("execution", result)
    assert paths == {"json": "report.json"}


def test_llm_adapter_is_text_only_when_disabled() -> None:
    assert LLMAssistantAgent(False, None, "test").explain_errors([]) == "LLM mode is disabled."
