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