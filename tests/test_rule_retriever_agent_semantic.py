from pathlib import Path

import pytest

from agents.rule_retriever import RuleRetrieverAgent
from domain.rule_retriever import (
    RetrievedRuleMatch,
    RuleQuery,
    SemanticRulePack,
)
from repositories.rules import RuleRepository


class StubSemanticRetriever:
    def __init__(self) -> None:
        self.queries: list[RuleQuery] = []

    def search(self, query: RuleQuery) -> SemanticRulePack:
        self.queries.append(query)
        return SemanticRulePack(
            query=query,
            matches=(
                RetrievedRuleMatch(
                    rule_id="fashion.descriptive.1",
                    content="Color should not contain unnecessary whitespace.",
                    score=0.91,
                    category="Fashion",
                    metadata={
                        "source_kind": "descriptive",
                        "executable": False,
                    },
                ),
            ),
        )


def test_rule_retriever_agent_search_delegates_to_semantic_retriever() -> None:
    semantic_retriever = StubSemanticRetriever()
    agent = RuleRetrieverAgent(
        RuleRepository(Path("rules_library.yaml")),
        semantic_retriever,
    )

    query = RuleQuery(
        query="remove unnecessary whitespace from color field",
        category="Fashion",
        top_k=3,
    )

    result = agent.search(query)

    assert result.query == query
    assert len(result.matches) == 1
    assert result.matches[0].rule_id == "fashion.descriptive.1"
    assert result.matches[0].metadata["executable"] is False
    assert semantic_retriever.queries == [query]


def test_rule_retriever_agent_requires_semantic_retriever_for_search() -> None:
    agent = RuleRetrieverAgent(
        RuleRepository(Path("rules_library.yaml")),
    )

    with pytest.raises(
        RuntimeError,
        match="requires a semantic rule retriever",
    ):
        agent.search(
            RuleQuery(query="find a relevant pricing rule")
        )


def test_rule_retriever_agent_preserves_legacy_retrieve_contract() -> None:
    agent = RuleRetrieverAgent(
        RuleRepository(Path("rules_library.yaml")),
    )

    rules, version = agent.retrieve("Fashion")

    assert rules.category == "Fashion"
    assert version
