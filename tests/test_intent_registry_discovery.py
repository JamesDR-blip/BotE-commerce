from domain.capability_registry import CapabilityRegistry
from domain.capabilities import CapabilitySpec
from domain.intent_resolver import IntentResolver


class FakeCapability:

    def __init__(self, spec):
        self.spec = spec


def test_intent_resolver_discovers_from_registry():

    registry = CapabilityRegistry()

    registry.register(
        FakeCapability(
            CapabilitySpec(
                id="data.mapping",
                version="1.0",
                description="Map marketplace data",
                input_keys=("frame",),
                output_keys=("mapped_frame",),
                intents=(
                    "map_marketplace_product",
                ),
            )
        )
    )

    resolver = IntentResolver.from_registry(
        registry
    )

    assert resolver.resolve(
        (
            "map_marketplace_product",
        )
    ) == (
        "data.mapping",
    )