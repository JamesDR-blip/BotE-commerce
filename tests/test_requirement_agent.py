from agents.requirement import RequirementAgent


def test_requirement_preserves_requested_capabilities():
    requirement = RequirementAgent().interpret(
        requested_category="fashion",
        requested_capabilities=(
            "data.clean",
            "data.extract",
            "data.validate",
        ),
    )

    assert requirement.requested_category == "fashion"
    assert requirement.requested_capabilities == (
        "data.clean",
        "data.extract",
        "data.validate",
    )


def test_requirement_defaults_to_no_capabilities():
    requirement = RequirementAgent().interpret()

    assert requirement.requested_category is None
    assert requirement.requested_capabilities == ()


def test_requirement_preserves_input_mappings():
    input_mappings = {
        "data.validate": {
            "frame": "cleaned_frame",
        },
    }

    requirement = RequirementAgent().interpret(
        requested_capabilities=("data.validate",),
        input_mappings=input_mappings,
    )

    assert requirement.input_mappings == input_mappings


def test_requirement_preserves_capability_parameters():
    parameters = {
        "data.extract": {
            "attributes": ("brand", "model", "color"),
        },
    }

    requirement = RequirementAgent().interpret(
        requested_capabilities=("data.extract",),
        parameters=parameters,
    )

    assert requirement.parameters == parameters