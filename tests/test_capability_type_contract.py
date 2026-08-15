from domain.capabilities import CapabilitySpec


def test_capability_spec_supports_input_types():
    spec = CapabilitySpec(
        id="data.clean",
        version="1.0",
        description="Clean data",
        input_keys=("frame",),
        output_keys=("frame",),
        input_types={
            "frame": object,
        },
    )

    assert spec.input_types["frame"] is object


def test_capability_spec_supports_output_types():
    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate data",
        input_keys=("frame",),
        output_keys=("result",),
        output_types={
            "result": object,
        },
    )

    assert spec.output_types["result"] is object