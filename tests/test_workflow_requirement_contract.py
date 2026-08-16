from agents.requirement import WorkflowRequirement


def test_workflow_requirement_supports_general_execution():

    requirement = WorkflowRequirement(
        requested_capabilities=(
            "data.clean",
            "data.extract",
        ),
        requested_intents=(
            "prepare_product_data",
        ),
        requested_category="Fashion",
    )

    assert requirement.requested_capabilities == (
        "data.clean",
        "data.extract",
    )

    assert requirement.requested_intents == (
        "prepare_product_data",
    )

    assert requirement.requested_category == "Fashion"