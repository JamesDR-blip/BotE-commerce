from agents.requirement import RequirementAgent
from agents.intent_classifier import IntentClassifier


def test_requirement_agent_builds_intent_from_text():

    classifier = IntentClassifier(
        {
            "assess_data_quality": (
                "kiểm tra chất lượng",
                "validate",
            )
        }
    )

    agent = RequirementAgent(
        classifier=classifier
    )

    requirement = agent.interpret(
        user_request=
        "Kiểm tra chất lượng dữ liệu sản phẩm"
    )

    assert requirement.requested_intents == (
        "assess_data_quality",
    )