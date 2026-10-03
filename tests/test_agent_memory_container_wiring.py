from configs.settings import Settings
from infrastructure.persistence.agent_memory_repository import (
    AgentMemoryRepository,
)
from services.container import Container


def test_container_wires_canonical_agent_memory_adapter_and_service(
    tmp_path,
    monkeypatch,
):
    class FakeRuleRetriever:
        def __init__(self, *, path):
            self.path = path

    monkeypatch.setattr(
        "services.container.ChromaRuleRetriever",
        FakeRuleRetriever,
    )

    container = Container(
        Settings(
            environment="test",
            database_url="sqlite://",
            rule_index_path=tmp_path / "rule-index",
            reports_path=tmp_path / "reports",
            dataset_storage_path=tmp_path / "datasets",
            marketplace_staging_path=tmp_path / "marketplace",
        )
    )

    assert type(container.memories) is AgentMemoryRepository
    assert type(container.memories).__module__ == (
        "infrastructure.persistence.agent_memory_repository"
    )
    assert container.agent_memory._memories is container.memories
    assert (
        container.agents.requirements._interpreter._parameter_resolver
        ._memory_service
        is container.agent_memory
    )
    assert (
        container.autonomous_operations_orchestrator._memory_service
        is container.agent_memory
    )
