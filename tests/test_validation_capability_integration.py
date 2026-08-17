from __future__ import annotations

import pandas as pd

from agents.requirement import ValidationRequirement
from configs.settings import Settings
from domain.models import ValidationResult
from services.container import Container


def test_validation_capability_executes_real_workflow():
    container = Container(Settings())

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
        }
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.qa",
        ),
    )

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
            "requested_category": None,
        },
        execution_id="integration-test",
    )

    validation_result = outputs.outputs["validation_result"]

    assert isinstance(validation_result, ValidationResult)
    assert validation_result.category
    assert isinstance(validation_result.issues, list)
    assert validation_result.clean is not None
    assert validation_result.quarantine is not None