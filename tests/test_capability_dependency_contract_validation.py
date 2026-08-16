import pytest

from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver
from domain.exceptions import (
    CapabilityDependencyContractError,
)


def test_dependency_contract_accepts_matching_outputs():

    capabilities = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("cleaned_frame",),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=("cleaned_frame",),
            output_keys=("result",),
            required_capabilities=(
                "data.clean",
            ),
        ),
    }

    result = DependencyResolver().resolve(
        requested=("data.validate",),
        capabilities=capabilities,
    )

    assert tuple(
        spec.id
        for spec in result
    ) == (
        "data.clean",
        "data.validate",
    )


def test_dependency_contract_rejects_missing_outputs():

    capabilities = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("wrong_output",),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=("cleaned_frame",),
            output_keys=("result",),
            required_capabilities=(
                "data.clean",
            ),
        ),
    }

    try:
        DependencyResolver().resolve(
            requested=("data.validate",),
            capabilities=capabilities,
        )
    except CapabilityDependencyContractError as exc:
        assert "cleaned_frame" in str(exc)
    else:
        raise AssertionError(
            "Expected CapabilityDependencyContractError"
        )


def test_dependency_contract_accepts_explicit_input_mapping():

    capabilities = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("cleaned_frame",),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=("frame",),
            output_keys=("result",),
            required_capabilities=(
                "data.clean",
            ),
            input_mappings=(
                ("frame", "cleaned_frame"),
            ),
        ),
    }

    result = DependencyResolver().resolve(
        requested=("data.validate",),
        capabilities=capabilities,
    )

    assert tuple(
        spec.id
        for spec in result
    ) == (
        "data.clean",
        "data.validate",
    )


def test_dependency_contract_rejects_invalid_explicit_input_mapping():

    capabilities = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("wrong_output",),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=("frame",),
            output_keys=("result",),
            required_capabilities=(
                "data.clean",
            ),
            input_mappings=(
                ("frame", "cleaned_frame"),
            ),
        ),
    }

    with pytest.raises(
        CapabilityDependencyContractError,
        match="cleaned_frame",
    ):
        DependencyResolver().resolve(
            requested=("data.validate",),
            capabilities=capabilities,
        )