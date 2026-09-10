"""Framework-independent contracts for semantic rule retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True)
class RuleQuery:
    """Semantic query describing the rule knowledge being requested."""

    query: str
    category: str | None = None
    fields: tuple[str, ...] = ()
    top_k: int = 5

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("Rule query cannot be empty")

        if self.category is not None and not self.category.strip():
            raise ValueError("Rule query category cannot be empty")

        if self.top_k < 1:
            raise ValueError("Rule query top_k must be at least 1")

        if len(set(self.fields)) != len(self.fields):
            raise ValueError("Rule query fields must be unique")


@dataclass(frozen=True)
class RetrievedRuleMatch:
    """One semantic match returned by a rule retriever."""

    rule_id: str
    content: str
    score: float
    category: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("Retrieved rule id cannot be empty")

        if not self.content.strip():
            raise ValueError("Retrieved rule content cannot be empty")

        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Retrieved rule score must be between 0 and 1")


@dataclass(frozen=True)
class SemanticRulePack:
    """Selected semantic rule matches for a query."""

    query: RuleQuery
    matches: tuple[RetrievedRuleMatch, ...] = ()

    def __post_init__(self) -> None:
        rule_ids = [match.rule_id for match in self.matches]

        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Semantic rule pack contains duplicate rule ids")


class RuleRetriever(Protocol):
    """Domain port for semantic rule retrieval."""

    def search(self, query: RuleQuery) -> SemanticRulePack:
        ...


__all__ = [
    "RuleQuery",
    "RetrievedRuleMatch",
    "SemanticRulePack",
    "RuleRetriever",
]
