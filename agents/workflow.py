"""Multi-agent data quality workflow. Agents never execute LLM-generated code."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from services.validation_service import ValidationService
from domain.models import ValidationIssue
from rule_engine.models import RuleSet
from .category import CategoryAgent
from .extraction import ExtractionAgent
from .qa import QAAgent
from .requirement import RequirementAgent
from .rule_retriever import RuleRetrieverAgent


class ClassifierAgent(CategoryAgent):
    pass


class AutoFixAgent:
    def fix(self, frame: pd.DataFrame, validator) -> pd.DataFrame: return validator.autofix(frame)


class ValidatorAgent:
    def __init__(self, service: ValidationService | None = None) -> None: self._service = service
    def validate(self, frame: pd.DataFrame, validator, rules: RuleSet) -> list[ValidationIssue]:
        return self._service.validate(frame, validator, rules)


class LLMExplanationAgent:
    """Optional explanation seam. Production adapters may call an LLM but return text only."""
    def explain(self, issues: list[ValidationIssue]) -> str:
        return f"Detected {len(issues)} deterministic validation issue(s)."


@dataclass
class Agents:
    requirements: RequirementAgent; classifier: CategoryAgent; rules: RuleRetrieverAgent; extraction: ExtractionAgent; fixer: AutoFixAgent; validator: ValidatorAgent; qa: QAAgent
