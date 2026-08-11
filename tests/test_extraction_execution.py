from __future__ import annotations

import pandas as pd

from agents.extraction import ExtractionAgent
from extractors.deterministic import DeterministicProductExtractor
from domain.capability_registry import CapabilityRegistry
from domain.capabilities import CapabilityContext
from domain.dependency_resolver import DependencyResolver
from services.capability_executor import CapabilityExecutor
from capabilities.extraction import ExtractionCapability


def test_data_extract_capability_executes_through_executor():
    registry = CapabilityRegistry()

    extraction_agent = ExtractionAgent(
        DeterministicProductExtractor()
    )

    registry.register(
        ExtractionCapability(extraction_agent)
    )

    executor = CapabilityExecutor(registry)

    from domain.plans import ExecutionPlan, PlanStep

    plan = ExecutionPlan(
        steps=(
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
        },
        execution_id="execution-extract-001",
    )

    assert "extractions" in result
    assert len(result["extractions"]) == 1

    extraction = result["extractions"][0]

    assert extraction.brand == "Nike"
    assert extraction.color == "Black"
    assert extraction.size == "XL"