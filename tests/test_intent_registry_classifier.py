from agents.intent_classifier import IntentClassifier
from domain.capability_registry import CapabilityRegistry
from domain.capabilities import (
    CapabilitySpec,
)


class FakeCapability:

    def __init__(self, spec):
        self.spec = spec

    def execute(self, context):
        pass


def test_intent_classifier_discovers_from_registry():

    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
                intents=(
                    "extract_product_attributes",
                ),
                intent_keywords={
                    "extract_product_attributes": (
                        "brand",
                        "model",
                    )
                },
            )
        )
    )

    classifier = IntentClassifier.from_registry(
        registry
    )

    intents = classifier.classify(
        "Lấy brand và model sản phẩm"
    )

    assert intents == (
        "extract_product_attributes",
    )