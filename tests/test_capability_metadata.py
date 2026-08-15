from domain.capabilities import CapabilitySpec


def test_capability_spec_supports_intents():
    spec = CapabilitySpec(
        id="data.extract",
        version="1.0",
        description="Extract product attributes",
        input_keys=("frame",),
        output_keys=("extractions",),
        intents=(
            "extract_attribute",
            "extract_brand",
            "extract_color",
        ),
    )

    assert spec.intents == (
        "extract_attribute",
        "extract_brand",
        "extract_color",
    )


def test_capability_spec_intents_default_empty():
    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate data",
        input_keys=("frame",),
        output_keys=("issues",),
    )

    assert spec.intents == ()