"""Rule retrieval agent for category-specific and semantic rule knowledge."""
from __future__ import annotations

from typing import Protocol

from domain.rule_retriever import (
    RuleQuery,
    RuleRetriever,
    SemanticRulePack,
)
from rule_engine.models import RuleSet


class RuleProvider(Protocol):
    def get(self, category: str) -> tuple[RuleSet, str]:
        ...


class RuleRetrieverAgent:
    def __init__(
        self,
        provider: RuleProvider,
        retriever: RuleRetriever | None = None,
    ) -> None:
        self._provider = provider
        self._retriever = retriever

    def retrieve(self, category: str) -> tuple[RuleSet, str]:
        """Retrieve executable validation rules by category.

        This legacy path remains backed by RuleProvider/RuleRepository.
        """
        return self._provider.get(category)

    def search(self, query: RuleQuery) -> SemanticRulePack:
        """Retrieve semantic rule knowledge without executing it."""

        if self._retriever is None:
            raise RuntimeError(
                "RuleRetrieverAgent requires a semantic rule retriever"
            )

        return self._retriever.search(query)
