from __future__ import annotations

import pytest

from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver
from domain.exceptions import (
    CapabilityDependencyCycleError,
    CapabilityDependencyMissingError,
)


def make_capability(
    capability_id: str,
    dependencies: tuple[str, ...] = (),
) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=(),
        output_keys=(),
        required_capabilities=dependencies,
    )


def test_dependency_resolver_resolves_single_dependency():
    resolver = DependencyResolver()

    capabilities = {
        "data.clean": make_capability("data.clean"),
        "data.validate": make_capability(
            "data.validate",
            ("data.clean",),
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


def test_dependency_resolver_resolves_nested_dependencies():
    resolver = DependencyResolver()

    capabilities = {
        "data.clean": make_capability("data.clean"),
        "data.validate": make_capability(
            "data.validate",
            ("data.clean",),
        ),
        "data.qa": make_capability(
            "data.qa",
            ("data.validate",),
        ),
    }

    result = resolver.resolve(
        requested=("data.qa",),
        capabilities=capabilities,
    )

    assert tuple(
        spec.id
        for spec in result
    ) == (
        "data.clean",
        "data.validate",
        "data.qa",
    )


def test_dependency_resolver_preserves_requested_order():
    resolver = DependencyResolver()

    capabilities = {
        "data.clean": make_capability("data.clean"),
        "data.extract": make_capability("data.extract"),
    }

    result = resolver.resolve(
        requested=(
            "data.clean",
            "data.extract",
        ),
        capabilities=capabilities,
    )

    assert tuple(
        spec.id
        for spec in result
    ) == (
        "data.clean",
        "data.extract",
    )


def test_dependency_resolver_rejects_missing_dependency():
    resolver = DependencyResolver()

    capabilities = {
        "data.validate": make_capability(
            "data.validate",
            ("data.clean",),
        ),
    }

    with pytest.raises(
        CapabilityDependencyMissingError,
    ):
        resolver.resolve(
            requested=("data.validate",),
            capabilities=capabilities,
        )


def test_dependency_resolver_rejects_dependency_cycle():
    resolver = DependencyResolver()

    capabilities = {
        "data.a": make_capability(
            "data.a",
            ("data.b",),
        ),
        "data.b": make_capability(
            "data.b",
            ("data.a",),
        ),
    }

    with pytest.raises(
        CapabilityDependencyCycleError,
    ):
        resolver.resolve(
            requested=("data.a",),
            capabilities=capabilities,
        )