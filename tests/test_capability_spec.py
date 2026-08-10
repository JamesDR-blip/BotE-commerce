from domain.capabilities import CapabilitySpec


def test_capability_spec_supports_parameter_keys():
    spec = CapabilitySpec(
        id="data.extract",
        version="1.0",
        description="Extract product attributes.",
        input_keys=("frame",),
        output_keys=("extractions",),
        parameter_keys=("attributes",),
    )

    assert spec.parameter_keys == ("attributes",)


def test_capability_spec_parameter_keys_default_to_empty():
    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data.",
        input_keys=("frame",),
        output_keys=("validation_result",),
    )

    assert spec.parameter_keys == ()