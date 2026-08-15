"""QA capability adapter."""

from __future__ import annotations

import pandas as pd

from agents.qa import QAAgent
from domain.capabilities import (
    CapabilityContext,
    CapabilityResult,
    CapabilitySpec,
)
from domain.models import ValidationIssue


QA_CAPABILITY_SPEC = CapabilitySpec(
    id="data.qa",
    version="1.0",
    description="Produce the final validation result from validation issues.",
    input_keys=(
        "frame",
        "category",
        "issues",
        "rule_version",
    ),
    output_keys=(
        "validation_result",
    ),
    required_capabilities=(
        "data.validate",
    ),
    intents=(
        "generate_quality_report",
        "assess_data_quality",
    ),
)


class QACapability:
    """Expose the QA agent as a platform capability."""

    def __init__(self, agent: QAAgent) -> None:
        self._agent = agent

    @property
    def spec(self) -> CapabilitySpec:
        return QA_CAPABILITY_SPEC

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:
        frame = context.inputs["frame"]
        category = context.inputs["category"]
        issues = context.inputs["issues"]
        rule_version = context.inputs["rule_version"]

        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                "data.qa requires a pandas DataFrame"
            )

        if not isinstance(category, str):
            raise TypeError(
                "data.qa requires a string category"
            )

        if not isinstance(issues, list):
            raise TypeError(
                "data.qa requires a list of validation issues"
            )

        if not all(
            isinstance(issue, ValidationIssue)
            for issue in issues
        ):
            raise TypeError(
                "data.qa requires ValidationIssue objects"
            )

        if not isinstance(rule_version, str):
            raise TypeError(
                "data.qa requires a string rule_version"
            )

        result = self._agent.result(
            frame=frame,
            issues=issues,
            category=category,
            version=rule_version,
        )

        return CapabilityResult(
            outputs={
                "validation_result": result,
            }
        )


__all__ = [
    "QACapability",
    "QA_CAPABILITY_SPEC",
]