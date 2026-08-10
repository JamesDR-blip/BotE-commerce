from __future__ import annotations

import pandas as pd

from domain.models import ValidationResult
from domain.validation_workflow import ValidationWorkflow


def test_validation_workflow_contract_accepts_compatible_implementation():
    class FakeValidationWorkflow:
        def run(
            self,
            frame: pd.DataFrame,
            requested_category: str | None = None,
            execution_id: str | None = None,
        ) -> ValidationResult:
            return ValidationResult(
                category=requested_category or "unknown",
                clean=frame,
                quarantine=frame.iloc[0:0],
                issues=[],
                health_score=1.0,
                rule_version="test",
            )

    workflow: ValidationWorkflow = FakeValidationWorkflow()

    frame = pd.DataFrame({"product_title": ["Test Product"]})

    result = workflow.run(
        frame,
        requested_category="fashion",
        execution_id="test-execution",
    )

    assert result.category == "fashion"
    assert result.health_score == 1.0