from domain.capabilities import CapabilitySpec
from domain.capability_dependency import CapabilityDependency

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

def test_capability_spec_supports_versioned_dependencies():

    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data.",
        input_keys=("frame",),
        output_keys=("result",),
        required_capabilities=(
            CapabilityDependency(
                capability_id="data.clean",
                version_constraint=">=1.0",
            ),
        ),
    )

    dependency = spec.required_capabilities[0]

    assert dependency.capability_id == "data.clean"
    assert dependency.version_constraint == ">=1.0"


import pytest


def test_capability_spec_rejects_duplicate_input_keys():
    with pytest.raises(
        ValueError,
        match=r"(?i)duplicate input key",
    ):
        CapabilitySpec(
            id="test.duplicate-input",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame", "frame"),
            output_keys=("result",),
        )


def test_capability_spec_rejects_duplicate_output_keys():
    with pytest.raises(
        ValueError,
        match=r"(?i)duplicate output key",
    ):
        CapabilitySpec(
            id="test.duplicate-output",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result", "result"),
        )


def test_capability_spec_rejects_unknown_input_type_key():
    with pytest.raises(
        ValueError,
        match=r"(?i)input types reference unknown keys",
    ):
        CapabilitySpec(
            id="test.unknown-input-type",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
            input_types={
                "unknown": str,
            },
        )


def test_capability_spec_rejects_unknown_output_type_key():
    with pytest.raises(
        ValueError,
        match=r"(?i)output types reference unknown keys",
    ):
        CapabilitySpec(
            id="test.unknown-output-type",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
            output_types={
                "unknown": str,
            },
        )


def test_capability_spec_rejects_unknown_intent_keyword_intent():
    with pytest.raises(
        ValueError,
        match=r"(?i)intent keywords reference unknown intents",
    ):
        CapabilitySpec(
            id="test.unknown-intent-keyword",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
            intents=("validate",),
            intent_keywords={
                "extract": ("extract",),
            },
        )


def test_capability_spec_rejects_unknown_parameter_keyword_parameter():
    with pytest.raises(
        ValueError,
        match=r"(?i)parameter keywords reference unknown parameters",
    ):
        CapabilitySpec(
            id="test.unknown-parameter-keyword",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
            parameter_keys=("attributes",),
            parameter_keywords={
                "unknown": {
                    "extract": ("brand",),
                },
            },
        )


def test_capability_spec_rejects_empty_id():
    with pytest.raises(
        ValueError,
        match=r"(?i)capability id cannot be empty",
    ):
        CapabilitySpec(
            id="",
            version="1.0",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
        )


def test_capability_spec_rejects_empty_version():
    with pytest.raises(
        ValueError,
        match=r"(?i)capability version missing",
    ):
        CapabilitySpec(
            id="test.missing-version",
            version="",
            description="Invalid capability",
            input_keys=("frame",),
            output_keys=("result",),
        )


def test_capability_spec_supports_input_mappings():
    spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data.",
        input_keys=("frame",),
        output_keys=("result",),
        input_mappings=(
            ("frame", "cleaned_frame"),
        ),
    )

    assert spec.input_mappings == (
        ("frame", "cleaned_frame"),
    )