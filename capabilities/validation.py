"""Validation capability adapter."""

from __future__ import annotations

import pandas as pd

from agents.rule_retriever import RuleRetrieverAgent
from agents.workflow import ValidatorAgent
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.models import ValidationIssue
from plugins.registry import ValidatorRegistry


VALIDATION_CAPABILITY_SPEC = CapabilitySpec(
    id="data.validate",
    version="1.0",
    description="Validate ecommerce tabular data.",
    input_keys=(
        "frame",
        "category",
    ),
    output_keys=(
        "frame",
        "category",
        "issues",
        "rule_version",
    ),
    input_mappings=(
        ("frame", "frame"),
        ("category", "category"),
    ),
    required_capabilities=(
        "data.clean",
    ),
    intents=(
        "validate_product_quality",
        "check_data_quality",
        "assess_data_quality",
    ),
    intent_keywords={
        "validate_product_quality": (
            "validate",
            "kiểm tra dữ liệu",
            "kiểm định dữ liệu",
        ),
        "check_data_quality": (
            "check data",
            "kiểm tra data",
        ),
        "assess_data_quality": (
            "quality",
            "data quality",
            "chất lượng dữ liệu",
            "kiểm tra chất lượng",
            "đánh giá chất lượng",
        ),
    },
)


class ValidationCapability:
    """Expose deterministic validation as a platform capability."""

    def __init__(
        self,
        rules: RuleRetrieverAgent,
        validator: ValidatorAgent,
        registry: ValidatorRegistry,
    ) -> None:
        self._rules = rules
        self._validator = validator
        self._registry = registry

    @property
    def spec(self) -> CapabilitySpec:
        return VALIDATION_CAPABILITY_SPEC

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        frame = context.inputs["frame"]
        category = context.inputs["category"]

        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                "data.validate requires a pandas DataFrame"
            )

        if not isinstance(category, str):
            raise TypeError(
                "data.validate requires a string category"
            )

        rules, rule_version = self._rules.retrieve(category)

        validator = self._registry.get(category)

        issues = self._validator.validate(
            frame,
            validator,
            rules,
        )

        if not isinstance(issues, list):
            raise TypeError(
                "validator must return a list of ValidationIssue"
            )

        if not all(
            isinstance(issue, ValidationIssue)
            for issue in issues
        ):
            raise TypeError(
                "validator must return ValidationIssue objects"
            )

        return CapabilityResult(
            outputs={
                "frame": frame,
                "category": category,
                "issues": issues,
                "rule_version": rule_version,
            }
        )


__all__ = [
    "ValidationCapability",
    "VALIDATION_CAPABILITY_SPEC",
]