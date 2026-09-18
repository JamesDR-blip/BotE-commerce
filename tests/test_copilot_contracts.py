from application.copilot.contracts import (
    CopilotAction,
    CopilotResponse,
)


def test_copilot_action_is_immutable():
    action = CopilotAction(
        action="get_health",
        arguments={"dataset_id": "ds-1"},
    )

    assert action.action == "get_health"
    assert action.arguments == {"dataset_id": "ds-1"}


def test_copilot_response_defaults_to_no_actions():
    response = CopilotResponse(
        message="Dataset health is available.",
    )

    assert response.message == "Dataset health is available."
    assert response.actions == ()


def test_copilot_response_preserves_actions():
    action = CopilotAction(
        action="get_diagnostics",
        arguments={"dataset_id": "ds-1"},
    )

    response = CopilotResponse(
        message="I found diagnostics.",
        actions=(action,),
    )

    assert response.actions == (action,)
