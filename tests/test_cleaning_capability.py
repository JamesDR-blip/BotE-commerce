import pandas as pd

from capabilities.cleaning import CleaningCapability
from domain.capabilities import CapabilityContext
from services.data_operations import DataOperationsService


class FakeClassifier:
    def classify(
        self,
        frame,
        categories,
        requested_category,
    ):
        return "Fashion"


class FakeFixer:
    def fix(self, frame, validator):
        result = frame.copy()
        result["cleaned"] = True
        return result


class FakeAgents:
    def __init__(self):
        self.classifier = FakeClassifier()
        self.fixer = FakeFixer()


class FakeRegistry:
    def categories(self):
        return ["Fashion"]

    def get(self, category):
        return object()


def test_cleaning_capability_returns_cleaned_frame_and_category():
    service = DataOperationsService(
        agents=FakeAgents(),
        registry=FakeRegistry(),
    )

    capability = CleaningCapability(service)

    frame = pd.DataFrame(
        {
            "product_title": ["Nike Air Max"],
        }
    )

    result = capability.execute(
        CapabilityContext(
            execution_id="test-execution",
            inputs={
                "frame": frame,
                "requested_category": "Fashion",
            },
        )
    )

    assert result.outputs["requested_category"] == "Fashion"

    cleaned_frame = result.outputs["frame"]

    assert isinstance(cleaned_frame, pd.DataFrame)
    assert cleaned_frame["cleaned"].tolist() == [True]