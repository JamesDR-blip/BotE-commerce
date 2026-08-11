from __future__ import annotations

import pandas as pd

from agents.extraction import ExtractionAgent
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from extractors.deterministic import DeterministicProductExtractor
from services.capability_executor import CapabilityExecutor


class FakeClassifier:
    def classify(
        self,
        frame,
        categories,
        requested_category=None,
    ):
        return requested_category or "Fashion"


class FakeFixer:
    def fix(self, frame, validator):
        return frame.assign(cleaned=True)


class FakeAgents:
    classifier = FakeClassifier()
    fixer = FakeFixer()


class FakeRegistry:
    def categories(self):
        return ("Fashion",)

    def get(self, category):
        return object()


def test_clean_output_is_passed_to_extract_capability():
    registry = CapabilityRegistry()

    cleaning = CleaningCapability(
        service=__import__(
            "services.data_operations",
            fromlist=["DataOperationsService"],
        ).DataOperationsService(
            agents=FakeAgents(),
            registry=FakeRegistry(),
        )
    )

    extraction = ExtractionCapability(
        ExtractionAgent(
            DeterministicProductExtractor()
        )
    )

    registry.register(cleaning)
    registry.register(extraction)

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="data.extract",
                capability_version="1.0",
            ),
        )
    )

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max Black XL",
            ],
        }
    )

    result = executor.execute(
        plan=plan,
        inputs={
            "frame": frame,
            "requested_category": "Fashion",
        },
        execution_id="execution-clean-extract-001",
    )

    assert "frame" in result
    assert result["requested_category"] == "Fashion"

    assert "extractions" in result
    assert len(result["extractions"]) == 1

    extracted = result["extractions"][0]

    assert extracted.brand == "Nike"
    assert extracted.color == "Black"
    assert extracted.size == "XL"

    # Verify extraction operated on the cleaned frame.
    assert "cleaned" in result["frame"].columns