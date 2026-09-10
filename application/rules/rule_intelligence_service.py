"""Application service for semantic rule intelligence."""

from __future__ import annotations

from domain.rule_retriever import RuleQuery, RuleRetriever, SemanticRulePack
from rule_engine.models import RuleSet


class RuleIntelligenceService:
    """Coordinate semantic rule retrieval for application use cases."""

    def __init__(
        self,
        *,
        retriever: RuleRetriever,
    ) -> None:
        self._retriever = retriever

    def sync(
        self,
        *,
        rule_sets: list[RuleSet],
        rule_version: str,
    ) -> int:
        """Synchronize semantic rule knowledge with the source rule version."""

        sync = getattr(self._retriever, "sync_rule_sets", None)

        if sync is None:
            raise TypeError(
                "Rule retriever does not support index synchronization"
            )

        return sync(
            rule_sets,
            rule_version=rule_version,
        )

    def search(
        self,
        *,
        query: RuleQuery,
    ) -> SemanticRulePack:
        return self._retriever.search(query)

    def recommend(
        self,
        *,
        query: RuleQuery,
        min_score: float = 0.0,
    ) -> SemanticRulePack:
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")

        result = self._retriever.search(query)

        matches = tuple(
            match
            for match in result.matches
            if match.score >= min_score
        )

        return SemanticRulePack(
            query=result.query,
            matches=matches,
        )


__all__ = ["RuleIntelligenceService"]
