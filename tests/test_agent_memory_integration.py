from datetime import datetime, timezone
from uuid import uuid4

from agents.parameter_resolver import ParameterResolver
from agents.requirement import RequirementAgent
from agents.requirement_interpreter import RequirementInterpreter
from application.memory.memory_service import AgentMemoryService
from database.models import Base, UserRecord, WorkspaceRecord, make_session_factory
from domain.agent_memory import CorrectionEvent
from domain.capabilities import CapabilitySpec
from repositories.agent_memory import AgentMemoryRepository


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


def make_agent():
    workspace_id = str(uuid4())
    user_id = str(uuid4())

    sessions = make_session_factory(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(
        sessions.kw["bind"]
    )

    memory_repository = AgentMemoryRepository(sessions)
    memory_service = AgentMemoryService(
        memories=memory_repository
    )

    resolver = ParameterResolver(
        memory_service=memory_service
    )

    interpreter = RequirementInterpreter(
        classifier=None,
        intent_resolver=None,
        parameter_resolver=resolver,
        catalog=make_catalog(),
    )

    agent = RequirementAgent(
        interpreter=interpreter
    )

    return (
        agent,
        memory_service,
        workspace_id,
        user_id,
    )


def test_requirement_agent_uses_persisted_correction():
    (
        agent,
        memory_service,
        workspace_id,
        user_id,
    ) = make_agent()

    memory_service.record_correction(
        CorrectionEvent(
            workspace_id=workspace_id,
            user_id=user_id,
            correction_type="parameter",
            key="data.extract.attributes",
            previous_value={
                "attributes": ["brand"],
            },
            corrected_value={
                "attributes": ["brand", "size"],
            },
            context={
                "request": "extract product attributes",
            },
        )
    )

    requirement = agent.interpret(
        requested_capabilities=("data.extract",),
        user_request="extract brand",
        workspace_id=workspace_id,
        user_id=user_id,
    )

    assert requirement.parameters == {
        "data.extract": {
            "attributes": ["brand", "size"],
        }
    }


def test_requirement_agent_enforces_memory_tenant_isolation():
    (
        agent,
        memory_service,
        workspace_id,
        user_a,
    ) = make_agent()

    user_b = str(uuid4())

    memory_service.record_correction(
        CorrectionEvent(
            workspace_id=workspace_id,
            user_id=user_a,
            correction_type="parameter",
            key="data.extract.attributes",
            corrected_value={
                "attributes": ["brand", "size"],
            },
        )
    )

    memory_service.record_correction(
        CorrectionEvent(
            workspace_id=workspace_id,
            user_id=user_b,
            correction_type="parameter",
            key="data.extract.attributes",
            corrected_value={
                "attributes": ["color"],
            },
        )
    )

    requirement_a = agent.interpret(
        requested_capabilities=("data.extract",),
        user_request="extract brand",
        workspace_id=workspace_id,
        user_id=user_a,
    )

    requirement_b = agent.interpret(
        requested_capabilities=("data.extract",),
        user_request="extract brand",
        workspace_id=workspace_id,
        user_id=user_b,
    )

    assert requirement_a.parameters == {
        "data.extract": {
            "attributes": ["brand", "size"],
        }
    }

    assert requirement_b.parameters == {
        "data.extract": {
            "attributes": ["color"],
        }
    }

    other_workspace = str(uuid4())

    requirement_other_workspace = agent.interpret(
        requested_capabilities=("data.extract",),
        user_request="extract brand",
        workspace_id=other_workspace,
        user_id=user_a,
    )

    assert requirement_other_workspace.parameters == {
        "data.extract": {
            "attributes": ["brand"],
        }
    }
