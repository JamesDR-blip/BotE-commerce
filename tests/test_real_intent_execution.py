import pandas as pd

from agents.requirement import ValidationRequirement
from configs.settings import Settings
from services.container import Container


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