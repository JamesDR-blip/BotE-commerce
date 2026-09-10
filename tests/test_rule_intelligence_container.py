from pathlib import Path

from application.rules.rule_intelligence_service import (
    RuleIntelligenceService,
)
from configs.settings import Settings
from infrastructure.rules.chroma_rule_retriever import ChromaRuleRetriever
from services.container import Container


def test_container_exposes_rule_intelligence(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        rule_index_path=tmp_path / "chroma",
    )

    container = Container(settings)

    assert isinstance(
        container.rule_retriever,
        ChromaRuleRetriever,
    )
    assert isinstance(
        container.rule_intelligence,
        RuleIntelligenceService,
    )
    assert container.rule_retriever._embedding_function is None
