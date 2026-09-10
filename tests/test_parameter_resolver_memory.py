from agents.parameter_resolver import ParameterResolver
from domain.agent_memory import AgentMemory
from domain.capabilities import CapabilitySpec


class FakeMemoryService:
    def __init__(self, memories):
        self.memories = memories
        self.queries = []

    def query(
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
            }
        )
        return self.memories


def make_catalog():
    return {
        "data.extract": CapabilitySpec(
            id="data.extract",
            version="1.0",
            description="Extract",
            input_keys=("frame",),
            output_keys=("extractions",),
            parameter_keys=("attributes",),
            parameter_keywords={
                "attributes": {
                    "brand": ("brand",),
                    "model": ("model",),
                    "color": ("color",),
                    "size": ("size",),
                }
            },
        )
    }


def make_memory(corrected_value, key="data.extract.attributes"):
    return AgentMemory(
        memory_id="memory-1",
        workspace_id="workspace-a",
        user_id="user-a",
        memory_type="correction",
        key=key,
        value={
            "previous_value": {"attributes": ["brand"]},
            "corrected_value": corrected_value,
            "context": {},
        },
        created_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )


def test_parameter_resolver_preserves_existing_behavior_without_memory():
    resolver = ParameterResolver()

    parameters = resolver.resolve(
        text="extract brand and model from product title",
        capabilities=("data.extract",),
        catalog=make_catalog(),
    )

    assert parameters == {
        "data.extract": {
            "attributes": ["brand", "model"],
        }
    }


def test_parameter_resolver_applies_prior_correction():
    memory_service = FakeMemoryService(
        [
            make_memory(
                {"attributes": ["brand", "size"]}
            )
        ]
    )

    resolver = ParameterResolver(memory_service=memory_service)

    parameters = resolver.resolve(
        text="extract brand from product title",
        capabilities=("data.extract",),
        catalog=make_catalog(),
        workspace_id="workspace-a",
        user_id="user-a",
    )

    assert parameters == {
        "data.extract": {
            "attributes": ["brand", "size"],
        }
    }

    assert memory_service.queries == [
        {
            "workspace_id": "workspace-a",
            "user_id": "user-a",
            "memory_type": "correction",
            "key": None,
        }
    ]


def test_parameter_resolver_ignores_invalid_memory_value():
    memory_service = FakeMemoryService(
        [
            make_memory(
                {"attributes": ["brand", "unknown_attribute"]}
            )
        ]
    )

    resolver = ParameterResolver(memory_service=memory_service)

    parameters = resolver.resolve(
        text="extract brand from product title",
        capabilities=("data.extract",),
        catalog=make_catalog(),
        workspace_id="workspace-a",
        user_id="user-a",
    )

    assert parameters == {
        "data.extract": {
            "attributes": ["brand"],
        }
    }


def test_parameter_resolver_ignores_memory_for_other_capability():
    memory_service = FakeMemoryService(
        [
            make_memory(
                {"attributes": ["brand"]},
                key="data.normalize.fields",
            )
        ]
    )

    resolver = ParameterResolver(memory_service=memory_service)

    parameters = resolver.resolve(
        text="extract brand from product title",
        capabilities=("data.extract",),
        catalog=make_catalog(),
        workspace_id="workspace-a",
        user_id="user-a",
    )

    assert parameters == {
        "data.extract": {
            "attributes": ["brand"],
        }
    }


def test_parameter_resolver_does_not_query_memory_without_tenant_scope():
    memory_service = FakeMemoryService([])

    resolver = ParameterResolver(memory_service=memory_service)

    parameters = resolver.resolve(
        text="extract brand from product title",
        capabilities=("data.extract",),
        catalog=make_catalog(),
    )

    assert parameters == {
        "data.extract": {
            "attributes": ["brand"],
        }
    }
    assert memory_service.queries == []
