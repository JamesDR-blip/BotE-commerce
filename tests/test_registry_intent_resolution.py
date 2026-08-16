from domain.intent_resolver import IntentResolver
from domain.capability_registry import CapabilityRegistry
from domain.capabilities import CapabilitySpec


class FakeCapability:

    def __init__(self, spec):
        self.spec = spec


def test_intent_resolver_discovers_capabilities_from_registry():

    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.translate",
                version="1.0",
                description="Translate product data",
                input_keys=(
                    "frame",
                ),
                output_keys=(
                    "frame",
                ),
                intents=(
                    "translate_product_data",
                ),
            )
        )
    )

    resolver = IntentResolver.from_registry(
        registry
    )

    result = resolver.resolve(
        (
            "translate_product_data",
        )
    )

    assert result == (
        "data.translate",
    )