from agents.requirement import WorkflowRequirement
from services.requirement_serializer import RequirementSerializer


def test_requirement_round_trip() -> None:
    original = WorkflowRequirement(
        requested_category="electronics",
        requested_capabilities=(
            "data.clean",
            "data.normalize",
            "data.extract",
        ),
        requested_intents=("clean_product_data",),
        input_mappings={
            "frame": {
                "product_title": "title",
            }
        },
        parameters={
            "data.clean": {
                "remove_duplicates": True,
            },
            "data.extract": {
                "attributes": ["brand", "model"],
            },
        },
    )

    serialized = RequirementSerializer.to_dict(original)
    restored = RequirementSerializer.from_dict(serialized)

    assert restored == original


def test_requirement_serialization_converts_tuples_to_lists() -> None:
    requirement = WorkflowRequirement(
        requested_capabilities=("data.clean",),
        requested_intents=("clean_product_data",),
    )

    data = RequirementSerializer.to_dict(requirement)

    assert data["requested_capabilities"] == ["data.clean"]
    assert data["requested_intents"] == ["clean_product_data"]


def test_requirement_deserialization_defaults() -> None:
    requirement = RequirementSerializer.from_dict({})

    assert requirement.requested_category is None
    assert requirement.requested_capabilities == ()
    assert requirement.requested_intents == ()
    assert requirement.input_mappings is None
    assert requirement.parameters is None