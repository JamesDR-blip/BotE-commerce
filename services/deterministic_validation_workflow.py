"""Deterministic implementation of the validation workflow contract."""

from __future__ import annotations

import pandas as pd

from agents.category import CategoryAgent
from agents.extraction import ExtractionAgent
from agents.qa import QAAgent
from agents.requirement import RequirementAgent
from agents.rule_retriever import RuleRetrieverAgent
from agents.workflow import AutoFixAgent, ValidatorAgent
from domain.models import ValidationResult
from domain.validation_workflow import ValidationWorkflow
from plugins.registry import ValidatorRegistry


class DeterministicValidationWorkflow:
    """Execute validation without requiring LangGraph."""

    def __init__(
        self,
        *,
        requirements: RequirementAgent,
        classifier: CategoryAgent,
        rules: RuleRetrieverAgent,
        extraction: ExtractionAgent,
        fixer: AutoFixAgent,
        validator: ValidatorAgent,
        qa: QAAgent,
        registry: ValidatorRegistry,
    ) -> None:
        self._requirements = requirements
        self._classifier = classifier
        self._rules = rules
        self._extraction = extraction
        self._fixer = fixer
        self._validator = validator
        self._qa = qa
        self._registry = registry

    def run(
        self,
        frame: pd.DataFrame,
        requested_category: str | None = None,
        execution_id: str | None = None,
    ) -> ValidationResult:
        requirement = self._requirements.interpret(
            requested_category=requested_category,
        )

        category = self._classifier.classify(
            frame,
            self._registry.categories(),
            requirement.requested_category,
        )

        rules, rule_version = self._rules.retrieve(category)

        # Preserve the current workflow contract.
        # Extraction is intentionally executed even though the current
        # validation result does not consume it yet.
        self._extraction.extract(frame)

        validator = self._registry.get(category)

        fixed_frame = self._fixer.fix(
            frame,
            validator,
        )

        issues = self._validator.validate(
            fixed_frame,
            validator,
            rules,
        )

        return self._qa.result(
            fixed_frame,
            issues,
            category,
            rule_version,
        )


__all__ = ["DeterministicValidationWorkflow"]