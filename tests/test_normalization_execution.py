from __future__ import annotations

import pandas as pd

from agents.extraction import ExtractionAgent
from capabilities.cleaning import CleaningCapability
from capabilities.extraction import ExtractionCapability
from capabilities.normalization import NormalizationCapability
from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from extractors.deterministic import DeterministicProductExtractor
from execution.capabilities.capability_executor import CapabilityExecutor
from services.data_operations import DataOperationsService
from domain.catalog.normalization import NormalizationService


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
        return frame.copy()


class FakeAgents:
    classifier = FakeClassifier()
    fixer = FakeFixer()


class FakeRegistry:
    def categories(self):
        return ("Fashion",)

    def get(self, category):
        return object()


def test_clean_normalize_extract_capability_chain():
    registry = CapabilityRegistry()

    cleaning = CleaningCapability(
        DataOperationsService(
            agents=FakeAgents(),
            registry=FakeRegistry(),
        )
    )

    normalization = NormalizationCapability(
        NormalizationService()
    )

    extraction = ExtractionCapability(
        ExtractionAgent(
            DeterministicProductExtractor()
        )
    )

    registry.register(cleaning)
    registry.register(normalization)
    registry.register(extraction)

    executor = CapabilityExecutor(registry)

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="data.clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="data.normalize",
                capability_version="1.0",
                parameters={
                    "fields": (
                        "product_title",
                    ),
                },
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
                "  Nike   Air   Max   Black   XL  ",
            ],
        }
    )

    result = executor.execute(
        plan=plan,
        inputs={
            "frame": frame,
            "requested_category": "Fashion",
        },
        execution_id="normalization-chain-001",
    )

    assert result["category"] == "Fashion"

    assert result["frame"]["product_title"].tolist() == [
        "Nike Air Max Black XL"
    ]

    assert "extractions" in result
    assert len(result["extractions"]) == 1

    extraction = result["extractions"][0]

    assert extraction.brand == "Nike"
    assert extraction.color == "Black"
    assert extraction.size == "XL"

    # The original input must remain unchanged.
    assert frame["product_title"].tolist() == [
        "  Nike   Air   Max   Black   XL  "
    ]


