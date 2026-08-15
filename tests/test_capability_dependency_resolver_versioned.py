from domain.capability_dependency import CapabilityDependency
from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec


def test_resolver_supports_versioned_dependency():

    resolver = DependencyResolver()

    capabilities = {
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
                    version_constraint=">=1.0",
                ),
            ),
        ),
    }

    result = resolver.resolve(
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