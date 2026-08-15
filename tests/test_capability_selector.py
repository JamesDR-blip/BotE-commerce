from __future__ import annotations

from agents.requirement import ValidationRequirement
from domain.capability_selector import CapabilitySelector


def test_selector_preserves_explicit_requested_capabilities():
    selector = CapabilitySelector(
        available_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
            "data.validate",
        )
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        )
    )

    selected = selector.select(requirement)

    assert selected == (
        "data.clean",
        "data.normalize",
        "data.extract",
    )


def test_selector_rejects_unknown_requested_capability():
    selector = CapabilitySelector(
        available_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        )
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.unknown",
        )
    )

    try:
        selector.select(requirement)
    except ValueError as exc:
        assert "data.unknown" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_selector_returns_empty_selection_when_nothing_requested():
    selector = CapabilitySelector(
        available_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        )
    )

    requirement = ValidationRequirement()

    assert selector.select(requirement) == ()


def test_selector_preserves_requested_order_and_duplicates():
    selector = CapabilitySelector(
        available_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        )
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.extract",
            "data.clean",
            "data.extract",
        )
    )

    selected = selector.select(requirement)

    assert selected == (
        "data.extract",
        "data.clean",
        "data.extract",
    )


def test_selector_reads_dynamic_capability_catalog():
    capabilities = ["data.clean"]

    selector = CapabilitySelector(
        available_capabilities=lambda: capabilities,
    )

    initial = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    assert selector.select(initial) == ("data.clean",)

    capabilities.append("data.extract")

    updated = ValidationRequirement(
        requested_capabilities=("data.extract",),
    )

    assert selector.select(updated) == ("data.extract",)