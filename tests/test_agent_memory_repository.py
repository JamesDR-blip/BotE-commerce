from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database.models import Base, UserRecord, WorkspaceRecord
from domain.agent_memory import AgentMemory
from repositories.agent_memory import AgentMemoryRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _repository():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    return (
        AgentMemoryRepository(sessions),
        sessions,
    )


def _memory(
    memory_id: str,
    workspace_id: str,
    user_id: str,
    *,
    memory_type: str = "correction",
    key: str = "category",
    expires_at=None,
):
    return AgentMemory(
        memory_id=memory_id,
        workspace_id=workspace_id,
        user_id=user_id,
        memory_type=memory_type,
        key=key,
        value={"value": "approved"},
        created_at=(expires_at - timedelta(seconds=1) if expires_at is not None else datetime.now(timezone.utc)),
        expires_at=expires_at,
    )


def test_agent_memory_repository_persists_and_reads_by_scope():
    repository, sessions = _repository()

    with sessions() as session:
        user = UserRecord(
            id="user-1",
            email="memory-user@example.com",
            display_name="Memory User",
        )
        session.add(user)
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="Memory Workspace",
            )
        )
        session.commit()

    repository.create(
        _memory(
            "memory-1",
            "workspace-1",
            "user-1",
        )
    )

    memories = repository.list_for_scope(
        workspace_id="workspace-1",
        user_id="user-1",
    )

    assert [memory.memory_id for memory in memories] == ["memory-1"]
    assert memories[0].value == {"value": "approved"}


def test_agent_memory_repository_enforces_user_isolation():
    repository, sessions = _repository()

    with sessions() as session:
        session.add_all(
            [
                UserRecord(
                    id="user-1",
                    email="memory-user-1@example.com",
                    display_name="User 1",
                ),
                UserRecord(
                    id="user-2",
                    email="memory-user-2@example.com",
                    display_name="User 2",
                ),
            ]
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="Memory Workspace",
            )
        )
        session.commit()

    repository.create(
        _memory(
            "memory-user-1",
            "workspace-1",
            "user-1",
        )
    )

    assert repository.list_for_scope(
        workspace_id="workspace-1",
        user_id="user-2",
    ) == []


def test_agent_memory_repository_enforces_workspace_isolation():
    repository, sessions = _repository()

    with sessions() as session:
        session.add_all(
            [
                UserRecord(
                    id="user-1",
                    email="memory-workspace@example.com",
                    display_name="User 1",
                ),
                WorkspaceRecord(
                    id="workspace-1",
                    owner_id="user-1",
                    name="Workspace 1",
                ),
                WorkspaceRecord(
                    id="workspace-2",
                    owner_id="user-1",
                    name="Workspace 2",
                ),
            ]
        )
        session.commit()

    repository.create(
        _memory(
            "memory-workspace-1",
            "workspace-1",
            "user-1",
        )
    )

    assert repository.list_for_scope(
        workspace_id="workspace-2",
        user_id="user-1",
    ) == []


def test_agent_memory_repository_filters_expired_memory():
    repository, sessions = _repository()
    now = datetime.now(timezone.utc)

    with sessions() as session:
        session.add(
            UserRecord(
                id="user-1",
                email="memory-expiry@example.com",
                display_name="User 1",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="Workspace",
            )
        )
        session.commit()

    repository.create(
        _memory(
            "expired",
            "workspace-1",
            "user-1",
            expires_at=now - timedelta(seconds=1),
        )
    )
    repository.create(
        _memory(
            "active",
            "workspace-1",
            "user-1",
            expires_at=now + timedelta(hours=1),
        )
    )

    memories = repository.list_for_scope(
        workspace_id="workspace-1",
        user_id="user-1",
        now=now,
    )

    assert [memory.memory_id for memory in memories] == ["active"]


def test_agent_memory_repository_evicts_expired_memory():
    repository, sessions = _repository()
    now = datetime.now(timezone.utc)

    with sessions() as session:
        session.add(
            UserRecord(
                id="user-1",
                email="memory-eviction@example.com",
                display_name="User 1",
            )
        )
        session.add(
            WorkspaceRecord(
                id="workspace-1",
                owner_id="user-1",
                name="Workspace",
            )
        )
        session.commit()

    repository.create(
        _memory(
            "expired",
            "workspace-1",
            "user-1",
            expires_at=now - timedelta(seconds=1),
        )
    )

    assert repository.evict_expired(now=now) == 1
    assert repository.list_for_scope(
        workspace_id="workspace-1",
        user_id="user-1",
        now=now,
    ) == []
