import pytest

from agents.planner import PlannerAgent
from agents.requirement import ValidationRequirement

from domain.capability_selector import CapabilitySelector
from domain.capability_registry import CapabilityRegistry
from domain.capabilities import CapabilitySpec
from domain.dependency_resolver import DependencyResolver
from domain.plans import ExecutionPlan

from capabilities.cleaning import CLEANING_CAPABILITY_SPEC
from capabilities.validation import VALIDATION_CAPABILITY_SPEC


class _FakeCapability:
    def __init__(self, spec: CapabilitySpec) -> None:
        self.spec = spec

class FakeCapability:
    spec = CapabilitySpec(
        id="test.fake",
        version="1.0",
        description="Fake capability",
        input_keys=(),
        output_keys=(),
    )

    def execute(self, context):
        raise NotImplementedError
    
class FakeCapabilityWithSpec:
    def __init__(self, spec: CapabilitySpec) -> None:
        self.spec = spec

    def execute(self, context):
        raise NotImplementedError
    
def make_spec(
    capability_id: str,
    required_capabilities: tuple[str, ...] = (),
) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=("frame",),
        output_keys=("result",),
        required_capabilities=required_capabilities,
    )


def make_catalog() -> dict[str, CapabilitySpec]:
    return {
        "data.clean": make_spec("data.clean"),
        "data.extract": make_spec("data.extract"),
        "data.validate": make_spec(
            "data.validate",
            required_capabilities=("data.clean",),
        ),
    }



def make_registry(
    catalog: dict[str, CapabilitySpec],
) -> CapabilityRegistry:
    registry = CapabilityRegistry()

    for spec in catalog.values():
        registry.register(
            FakeCapabilityWithSpec(spec)
        )

    return registry

def test_planner_builds_execution_plan_from_requested_capabilities():
    planner = PlannerAgent(
        registry=make_registry(make_catalog()),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert isinstance(plan, ExecutionPlan)
    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_preserves_capability_versions():
    catalog = {
        "data.clean": CapabilitySpec(
            id="data.clean",
            version="2.0",
            description="Clean data",
            input_keys=("frame",),
            output_keys=("clean_frame",),
        ),
    }

    planner = PlannerAgent(
        registry=make_registry(catalog),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == "data.clean"
    assert plan.steps[0].capability_version == "2.0"


def test_planner_does_not_add_unrequested_capabilities():
    planner = PlannerAgent(
        registry=make_registry(make_catalog()),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
    ]


def test_planner_builds_plan_for_extraction_only():
    planner = PlannerAgent(
        registry=make_registry(make_catalog()),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.extract",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.extract",
    ]


def test_planner_composes_cleaning_and_extraction():
    planner = PlannerAgent(
        registry=make_registry(make_catalog()),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.clean",
            "data.extract",
        ),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.extract",
    ]


def test_planner_marks_plan_source():
    planner = PlannerAgent(
        registry=make_registry(make_catalog()),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
    )

    plan = planner.plan(requirement)

    assert plan.metadata["source"] == "planner"


def test_planner_can_build_plan_for_cleaning_and_validation():
    catalog = {
        CLEANING_CAPABILITY_SPEC.id: CLEANING_CAPABILITY_SPEC,
        VALIDATION_CAPABILITY_SPEC.id: VALIDATION_CAPABILITY_SPEC,
    }

    planner = PlannerAgent(
        registry=make_registry(catalog),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.validate",
        ),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_resolves_validation_dependencies():
    cleaning_spec = CapabilitySpec(
        id="data.clean",
        version="1.0",
        description="Clean ecommerce data",
        input_keys=("frame",),
        output_keys=("frame",),
    )

    validation_spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data",
        input_keys=("frame",),
        output_keys=("validation_result",),
        required_capabilities=("data.clean",),
    )

    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": cleaning_spec,
            "data.validate": validation_spec,
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]


def test_planner_preserves_explicit_input_mapping():
    cleaning_spec = CapabilitySpec(
        id="data.clean",
        version="1.0",
        description="Clean ecommerce data",
        input_keys=("frame",),
        output_keys=("cleaned_frame",),
    )

    validation_spec = CapabilitySpec(
        id="data.validate",
        version="1.0",
        description="Validate ecommerce data",
        input_keys=("frame",),
        output_keys=("validation_result",),
        required_capabilities=("data.clean",),
    )

    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": cleaning_spec,
            "data.validate": validation_spec,
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]

    # Planner hiện chưa được phép tự đoán mapping.
    assert plan.steps[0].input_mapping == {}
    assert plan.steps[1].input_mapping == {}


def test_planner_does_not_infer_input_mapping():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]

    assert plan.steps[0].input_mapping == {}
    assert plan.steps[1].input_mapping == {}

def test_planner_builds_explicit_input_mapping_between_capabilities():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
                input_mappings=(
                ("frame", "cleaned_frame"),
                ),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert [step.capability_id for step in plan.steps] == [
        "data.clean",
        "data.validate",
    ]

    assert plan.steps[1].input_mapping == {
        "frame": "cleaned_frame",
    }


def test_planner_does_not_infer_input_mapping_from_matching_output_names():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    plan = planner.plan(requirement)

    assert plan.steps[1].input_mapping == {}


def test_planner_preserves_requirement_input_mapping():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
        input_mappings={
            "data.validate": {
                "frame": "cleaned_frame",
            },
        },
    )

    plan = planner.plan(requirement)

    assert plan.steps[1].input_mapping == {
        "frame": "cleaned_frame",
    }


def test_planner_requirement_mapping_overrides_capability_mapping():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
                input_mappings=(
                    ("frame", "cleaned_frame"),
                ),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
        input_mappings={
            "data.validate": {
                "frame": "override_frame",
            },
        },
    )

    plan = planner.plan(requirement)

    assert plan.steps[1].input_mapping == {
        "frame": "override_frame",
    }


def test_planner_preserves_requirement_parameters():
    planner = PlannerAgent(
        registry=make_registry({
            "data.extract": CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
                parameter_keys=("attributes",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.extract",),
        parameters={
            "data.extract": {
                "attributes": ("brand", "model", "color"),
            },
        },
    )

    plan = planner.plan(requirement)

    assert plan.steps[0].parameters == {
        "attributes": ("brand", "model", "color"),
    }


def test_planner_reads_capabilities_from_registry():
    registry = CapabilityRegistry()

    registry.register(FakeCapability())

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.fake",),
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == ["test.fake"]


def test_planner_sees_capability_registered_after_planner_creation():
    registry = CapabilityRegistry()

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    registry.register(FakeCapability())

    requirement = ValidationRequirement(
        requested_capabilities=("test.fake",),
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == ["test.fake"]

def test_planner_default_selector_rejects_unknown_capability():
    registry = CapabilityRegistry()

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("test.unknown",),
    )

    try:
        planner.plan(requirement)
    except ValueError as exc:
        assert "test.unknown" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

def test_planner_uses_capability_selector():
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
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
            )
        )
    )

    selector = CapabilitySelector(
        available_capabilities=(
            "data.clean",
            "data.extract",
        )
    )

    planner = PlannerAgent(
        registry=registry,
        resolver=DependencyResolver(),
        selector=selector,
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.extract",
            "data.clean",
        )
    )

    plan = planner.plan(requirement)

    assert [
        step.capability_id
        for step in plan.steps
    ] == [
        "data.extract",
        "data.clean",
    ]


def test_planner_rejects_input_mapping_to_unknown_source():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("cleaned_frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("validation_result",),
                required_capabilities=("data.clean",),
                input_mappings=(
                    ("frame", "does_not_exist"),
                ),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.validate",),
    )

    with pytest.raises(ValueError, match=r"(?i)unknown input mapping source"):
        planner.plan(requirement)


def test_planner_allows_input_mapping_from_external_input():
    planner = PlannerAgent(
        registry=make_registry({
            "data.extract": CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
                input_mappings=(
                    ("frame", "frame"),
                ),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.extract",),
    )

    plan = planner.plan(requirement)

    assert plan.steps[0].input_mapping == {
        "frame": "frame",
    }


def test_planner_rejects_unknown_capability_parameters():
    planner = PlannerAgent(
        registry=make_registry({
            "data.extract": CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
                parameter_keys=("attributes",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.extract",),
        parameters={
            "data.extract": {
                "unknown_parameter": True,
            },
        },
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown parameter",
    ):
        planner.plan(requirement)


def test_planner_rejects_parameters_for_unrequested_capability():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            ),
            "data.extract": CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
                parameter_keys=("attributes",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
        parameters={
            "data.extract": {
                "attributes": ("brand",),
            },
        },
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)parameters.*not.*planned|not.*requested",
    ):
        planner.plan(requirement)


def test_planner_rejects_input_mapping_for_unrequested_capability():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            ),
            "data.extract": CapabilitySpec(
                id="data.extract",
                version="1.0",
                description="Extract data",
                input_keys=("frame",),
                output_keys=("extractions",),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=("data.clean",),
        input_mappings={
            "data.extract": {
                "frame": "frame",
            },
        },
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)mapping.*not.*planned|not.*requested",
    ):
        planner.plan(requirement)


def test_planner_expands_capability_dependencies():
    planner = PlannerAgent(
        registry=make_registry({
            "data.clean": CapabilitySpec(
                id="data.clean",
                version="1.0",
                description="Clean data",
                input_keys=("frame",),
                output_keys=("frame",),
            ),
            "data.validate": CapabilitySpec(
                id="data.validate",
                version="1.0",
                description="Validate data",
                input_keys=("frame",),
                output_keys=("issues",),
                required_capabilities=(
                    "data.clean",
                ),
            ),
            "data.qa": CapabilitySpec(
                id="data.qa",
                version="1.0",
                description="QA result",
                input_keys=("issues",),
                output_keys=("validation_result",),
                required_capabilities=(
                    "data.validate",
                ),
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.qa",
        ),
    )

    plan = planner.plan(requirement)

    assert tuple(
        step.capability_id
        for step in plan.steps
    ) == (
        "data.clean",
        "data.validate",
        "data.qa",
    )


def test_planner_rejects_invalid_capability_type_contract():
    planner = PlannerAgent(
        registry=make_registry({
            "data.bad": CapabilitySpec(
                id="data.bad",
                version="1.0",
                description="Bad contract",
                input_keys=("frame",),
                output_keys=("result",),
                input_types={
                    "frame": str,
                },
            ),
        }),
        resolver=DependencyResolver(),
    )

    requirement = ValidationRequirement(
        requested_capabilities=(
            "data.bad",
        ),
    )

    with pytest.raises(
        TypeError,
        match="input type",
    ):
        planner.plan(requirement)