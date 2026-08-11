import pandas as pd

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


def test_clean_classifies_and_fixes_frame():
    frame = pd.DataFrame(
        {
            "product_title": [" Nike Air Max "],
        }
    )

    service = DataOperationsService(
        agents=FakeAgents(),
        registry=FakeRegistry(),
    )

    category, cleaned = service.clean(
        frame,
        requested_category="Fashion",
    )

    assert category == "Fashion"
    assert cleaned["cleaned"].tolist() == [True]