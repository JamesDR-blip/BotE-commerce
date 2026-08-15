from __future__ import annotations

import pandas as pd

from configs.settings import Settings
from services.container import Container

from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement
from domain.capability_registry import CapabilityRegistry
from domain.dependency_resolver import DependencyResolver
from domain.capabilities import CapabilitySpec


def test_planner_composes_requested_capabilities_in_order():
    registry = CapabilityRegistry()

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            )
        )
    )

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.normalize",
                version="1.0",
                description="Normalize data",
                input_keys=("frame",),
                output_keys=("frame",),
                parameter_keys=("fields",),
            )
        )
    )

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract attributes",
                input_keys=("frame",),
                output_keys=("extractions",),
            )
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        ),
        parameters={
            "data.normalize": {
                "fields": (
                    "product_title",
                    "color",
                ),
            },
        },
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.normalize",
        "data.extract",
    ]

    assert plan.steps[1].parameters == {
        "fields": (
            "product_title",
            "color",
        ),
    }


class _FakeCapability:
    def __init__(self, spec: CapabilitySpec) -> None:
        self.spec = spec


def test_real_composed_pipeline_executes_clean_normalize_extract():
    container = Container(Settings())

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        ),
        parameters={
            "data.normalize": {
                "fields": (
                    "product_title",
                    "color",
                ),
            },
        },
    )

    frame = pd.DataFrame(
        {
            "product_title": [
                "  Nike   Air   Max   Black   XL  ",
            ],
            "color": [
                " black ",
            ],
        }
    )

    plan = container.planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.normalize",
        "data.extract",
    ]

    outputs = container.capability_execution.execute(
        requirement=requirement,
        inputs={
            "frame": frame,
            "requested_category": "Fashion",
        },
        execution_id="real-composed-pipeline-001",
    )

    assert outputs["frame"]["product_title"].tolist() == [
        "Nike Air Max Black XL"
    ]

    assert outputs["frame"]["color"].tolist() == [
        "Black"
    ]

    assert "extractions" in outputs
    assert len(outputs["extractions"]) == 1

    extraction = outputs["extractions"][0]

    assert extraction.brand == "Nike"
    assert extraction.color == "Black"
    assert extraction.size == "XL"

    # Original input must remain unchanged.
    assert frame["product_title"].tolist() == [
        "  Nike   Air   Max   Black   XL  "
    ]

    assert frame["color"].tolist() == [
        " black "
    ]


def test_planner_deduplicates_overlapping_requested_capabilities():
    registry = CapabilityRegistry()

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            )
        )
    )

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.normalize",
                version="1.0",
                description="Normalize data",
                input_keys=("frame",),
                output_keys=("frame",),
                required_capabilities=("data.clean",),
            )
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.normalize",
        ),
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.normalize",
    ]


def test_planner_composed_pipeline_preserves_explicit_input_mapping():
    registry = CapabilityRegistry()

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            )
        )
    )

    registry.register(
        _FakeCapability(
            CapabilitySpec(
                id="data.normalize",
                version="1.0",
                description="Normalize data",
                input_keys=("frame",),
                output_keys=("frame",),
                required_capabilities=("data.clean",),
                input_mappings=(
                    ("frame", "cleaned_frame"),
                ),
            )
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.normalize",),
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.clean",
        "data.normalize",
    ]

    assert plan.steps[1].input_mapping == {
        "frame": "cleaned_frame",
    }