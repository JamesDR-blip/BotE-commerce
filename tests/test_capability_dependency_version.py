from domain.capabilities import CapabilitySpec
from domain.dependencies import CapabilityDependency
from domain.dependency_resolver import DependencyResolver
from domain.exceptions import (
    CapabilityDependencyVersionError,
)


def test_dependency_accepts_matching_version():

    resolver = DependencyResolver()

    specs = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="2.0",
            description="clean",
            input_keys=(),
            output_keys=(),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=(),
            output_keys=(),
            required_capabilities=(
                CapabilityDependency(
                    capability_id="data.clean",
                    version_constraint=">=2.0",
                ),
            ),
        ),
    }

    result = resolver.resolve(
        requested=("data.validate",),
        capabilities=specs,
    )

    assert tuple(
        item.id
        for item in result
    ) == (
        "data.clean",
        "data.validate",
    )


def test_dependency_rejects_invalid_version():

    resolver = DependencyResolver()

    specs = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="1.0",
            description="clean",
            input_keys=(),
            output_keys=(),
        ),
        "data.validate": CapabilitySpec(
            id="data.validate",
            version="1.0",
            description="validate",
            input_keys=(),
            output_keys=(),
            required_capabilities=(
                CapabilityDependency(
                    capability_id="data.clean",
                    version_constraint=">=2.0",
                ),
            ),
        ),
    }

    try:
        resolver.resolve(
            requested=("data.validate",),
            capabilities=specs,
        )
    except CapabilityDependencyVersionError:
        return

    raise AssertionError(
        "Expected version constraint failure"
    )