from domain.capability_dependency import CapabilityDependency


def test_capability_dependency_supports_version_constraint():

    dependency = CapabilityDependency(
        capability_id="data.clean",
        version_constraint=">=1.0",
    )

    assert dependency.capability_id == "data.clean"
    assert dependency.version_constraint == ">=1.0"