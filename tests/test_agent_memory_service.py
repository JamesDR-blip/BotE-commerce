from datetime import datetime, timedelta, timezone

from application.memory.memory_service import AgentMemoryService
from application.memory.redaction import redact_memory_value
from domain.agent_memory import CorrectionEvent, ExecutionLearning


class FakeMemoryRepository:
    def __init__(self):
        self.created = []
        self.queries = []
        self.evictions = []

    def create(self, memory):
        self.created.append(memory)
        return memory

    def list_for_scope(
        self,
        *,
        workspace_id,
        user_id,
        memory_type=None,
        key=None,
        now=None,
    ):
        self.queries.append(
            {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "memory_type": memory_type,
                "key": key,
                "now": now,
            }
        )
        return []

    def evict_expired(self, *, now=None):
        self.evictions.append(now)
        return 2


def test_redact_memory_value_recursively_redacts_pii():
    value = {
        "category": "Fashion",
        "customer": {
            "email": "customer@example.com",
            "phone": "+84123456789",
            "name": "Customer Name",
        },
        "items": [
            {"product_name": "Nike Air Max"},
            {"customer_email": "nested@example.com"},
        ],
    }

    result = redact_memory_value(value)

    assert result["category"] == "Fashion"
    assert result["customer"]["email"] == "[REDACTED]"
    assert result["customer"]["phone"] == "[REDACTED]"
    assert result["customer"]["name"] == "Customer Name"
    assert result["items"][0]["product_name"] == "Nike Air Max"
    assert result["items"][1]["customer_email"] == "[REDACTED]"


def test_record_correction_redacts_values_and_context():
    repository = FakeMemoryRepository()
    service = AgentMemoryService(memories=repository)

    event = CorrectionEvent(
        workspace_id="workspace-a",
        user_id="user-a",
        correction_type="parameter_override",
        key="data.qa.threshold",
        previous_value={"email": "old@example.com", "threshold": 80},
        corrected_value={"email": "new@example.com", "threshold": 90},
        context={
            "customer_phone": "+84123456789",
            "category": "Fashion",
        },
    )

    memory = service.record_correction(
        event,
        memory_id="memory-1",
    )

    assert memory.memory_id == "memory-1"
    assert memory.workspace_id == "workspace-a"
    assert memory.user_id == "user-a"
    assert memory.memory_type == "correction"
    assert memory.key == "data.qa.threshold"

    assert memory.value["previous_value"]["email"] == "[REDACTED]"
    assert memory.value["previous_value"]["threshold"] == 80
    assert memory.value["corrected_value"]["email"] == "[REDACTED]"
    assert memory.value["corrected_value"]["threshold"] == 90
    assert memory.value["context"]["customer_phone"] == "[REDACTED]"
    assert memory.value["context"]["category"] == "Fashion"

    assert repository.created == [memory]


def test_record_learning_preserves_execution_reference_and_redacts_value():
    repository = FakeMemoryRepository()
    service = AgentMemoryService(memories=repository)

    learning = ExecutionLearning(
        workspace_id="workspace-a",
        user_id="user-a",
        execution_id="execution-1",
        key="fashion.size_mapping",
        value={
            "preferred_size": "42",
            "customer_email": "customer@example.com",
        },
        context={
            "category": "Fashion",
        },
    )

    memory = service.record_learning(
        learning,
        memory_id="memory-2",
    )

    assert memory.memory_type == "execution_learning"
    assert memory.key == "fashion.size_mapping"
    assert memory.value["execution_id"] == "execution-1"
    assert memory.value["value"]["preferred_size"] == "42"
    assert memory.value["value"]["customer_email"] == "[REDACTED]"
    assert memory.value["context"]["category"] == "Fashion"


def test_query_enforces_workspace_and_user_scope():
    repository = FakeMemoryRepository()
    service = AgentMemoryService(memories=repository)

    now = datetime.now(timezone.utc)

    assert service.query(
        workspace_id="workspace-a",
        user_id="user-a",
        memory_type="correction",
        key="data.qa.threshold",
        now=now,
    ) == []

    assert repository.queries == [
        {
            "workspace_id": "workspace-a",
            "user_id": "user-a",
            "memory_type": "correction",
            "key": "data.qa.threshold",
            "now": now,
        }
    ]


def test_evict_expired_delegates_to_repository():
    repository = FakeMemoryRepository()
    service = AgentMemoryService(memories=repository)

    now = datetime.now(timezone.utc)

    assert service.evict_expired(now=now) == 2
    assert repository.evictions == [now]


def test_record_correction_supports_ttl():
    repository = FakeMemoryRepository()
    service = AgentMemoryService(memories=repository)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    memory = service.record_correction(
        CorrectionEvent(
            workspace_id="workspace-a",
            user_id="user-a",
            correction_type="parameter_override",
            key="data.qa.threshold",
            corrected_value={"threshold": 95},
        ),
        memory_id="memory-ttl",
        expires_at=expires_at,
    )

    assert memory.expires_at == expires_at
    assert memory.expires_at > memory.created_at
