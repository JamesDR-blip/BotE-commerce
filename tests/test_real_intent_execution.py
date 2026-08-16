import pandas as pd

from agents.requirement import ValidationRequirement
from configs.settings import Settings
from services.container import Container
from domain.execution_status import ExecutionStatus


def test_real_intent_executes_quality_pipeline():

    container = Container(Settings())

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
            "size": [
                "42",
                "43",
            ],
            "color": [
                "Black",
                "White",
            ],
        }
    )

    requirement = ValidationRequirement(
        requested_intents=(
            "assess_data_quality",
        )
    )

    result = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
            "requested_category": "Fashion",
        },
        execution_id="test-intent-execution",
    )

    assert "validation_result" in result


def test_real_intent_executes_capabilities_in_dependency_order():

    container = Container(Settings())

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
            "size": [
                "42",
                "43",
            ],
            "color": [
                "Black",
                "White",
            ],
        }
    )

    requirement = ValidationRequirement(
        requested_intents=(
            "assess_data_quality",
        )
    )

    result, trace = (
        container.capability_execution.execute_with_trace(
            requirement=requirement,
            inputs={
                "frame": frame,
                "requested_category": "Fashion",
            },
            execution_id="test-intent-execution-order",
        )
    )

    assert "validation_result" in result

    capability_ids = [
        record.capability_id
        for record in trace.records
    ]

    assert capability_ids == [
        "data.clean",
        "data.validate",
        "data.qa",
    ]
    assert all(
        record.status.value == ExecutionStatus.COMPLETED
        for record in trace.records
    )