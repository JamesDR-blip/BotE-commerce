from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver
from domain.exceptions import (
    CapabilityDependencyCycleError,
    CapabilityDependencyMissingError,
)


def make_spec(
    capability_id: str,
    required_capabilities: tuple[str, ...] = (),
) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=(),
        output_keys=(),
        required_capabilities=required_capabilities,
    )


def test_resolves_capability_without_dependencies():
    catalog = {
        "data.clean": make_spec("data.clean"),
    }

    result = DependencyResolver().resolve(
        ["data.clean"],
        catalog,
    )

    assert [spec.id for spec in result] == [
        "data.clean",
    ]


def test_resolves_direct_dependency_before_capability():
    catalog = {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec(
            "data.extract",
            ("data.clean",),
        ),
    }

    result = DependencyResolver().resolve(
        ["data.extract"],
        catalog,
    )

    assert [spec.id for spec in result] == [
        "data.clean",
        "data.extract",
    ]


def test_resolves_transitive_dependencies():
    catalog = {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec(
            "data.extract",
            ("data.clean",),
        ),
        "shopify.map": make_spec(
            "shopify.map",
            ("data.extract",),
        ),
    }

    result = DependencyResolver().resolve(
        ["shopify.map"],
        catalog,
    )

    assert [spec.id for spec in result] == [
        "data.clean",
        "data.extract",
        "shopify.map",
    ]


def test_resolves_multiple_dependencies_deterministically():
    catalog = {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec("data.extract"),
        "shopify.map": make_spec(
            "shopify.map",
            ("data.clean", "data.extract"),
        ),
    }

    result = DependencyResolver().resolve(
        ["shopify.map"],
        catalog,
    )

    assert [spec.id for spec in result] == [
        "data.clean",
        "data.extract",
        "shopify.map",
    ]


def test_does_not_duplicate_shared_dependency():
    catalog = {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec(
            "data.extract",
            ("data.clean",),
        ),
        "data.validate": make_spec(
            "data.validate",
            ("data.clean",),
        ),
    }

    result = DependencyResolver().resolve(
        ["data.extract", "data.validate"],
        catalog,
    )

    assert [spec.id for spec in result] == [
        "data.clean",
        "data.extract",
        "data.validate",
    ]


def test_missing_dependency_raises():
    catalog = {
        "data.extract": make_spec(
            "data.extract",
            ("data.clean",),
        ),
    }

    try:
        DependencyResolver().resolve(
            ["data.extract"],
            catalog,
        )
    except CapabilityDependencyMissingError as exc:
        assert "data.clean" in str(exc)
    else:
        raise AssertionError(
            "Expected CapabilityDependencyMissingError"
        )


def test_cycle_raises():
    catalog = {
        "data.clean": make_spec(
            "data.clean",
            ("data.extract",),
        ),
        "data.extract": make_spec(
            "data.extract",
            ("data.clean",),
        ),
    }

    try:
        DependencyResolver().resolve(
            ["data.clean"],
            catalog,
        )
    except CapabilityDependencyCycleError as exc:
        assert "data.clean" in str(exc)
    else:
        raise AssertionError(
            "Expected CapabilityDependencyCycleError"
        )