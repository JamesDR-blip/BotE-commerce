"""Non-persistent application operations for uploaded tabular data."""
from __future__ import annotations

import pandas as pd

from agents.workflow import Agents
from extractors.base import ExtractedAttributes
from plugins.registry import ValidatorRegistry


class DataOperationsService:
    def __init__(self, agents: Agents, registry: ValidatorRegistry) -> None:
        self._agents = agents
        self._registry = registry

    def clean(self, frame: pd.DataFrame, requested_category: str | None = None) -> tuple[str, pd.DataFrame]:
        category = self._agents.classifier.classify(frame, self._registry.categories(), requested_category)
        return category, self._agents.fixer.fix(frame, self._registry.get(category))

    def extract(self, frame: pd.DataFrame) -> list[ExtractedAttributes]:
        return self._agents.extraction.extract(frame)
