from __future__ import annotations

import pandas as pd

from configs.settings import Settings
from services.container import Container
from capabilities.validation import ValidationCapability
from domain.capabilities import CapabilityContext
from domain.models import ValidationResult


def test_validation_capability_executes_real_workflow():
    container = Container(Settings())

    capability = ValidationCapability(container.workflow)

    frame = pd.DataFrame(
        {
            "product_title": [
                "Nike Air Max 90",
                "Adidas Ultraboost",
            ],
        }
    )

    context = CapabilityContext(
        execution_id="integration-test",
        inputs={
            "frame": frame,
            "requested_category": None,
        },
    )

    result = capability.execute(context)

    validation_result = result.outputs["validation_result"]

    assert isinstance(validation_result, ValidationResult)
    assert validation_result.category
    assert isinstance(validation_result.issues, list)
    assert validation_result.clean is not None
    assert validation_result.quarantine is not None