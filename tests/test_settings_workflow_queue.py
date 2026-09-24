from __future__ import annotations

import pytest

from configs.settings import Settings


def test_default_workflow_queue_backend_is_inprocess() -> None:
    settings = Settings()

    assert settings.workflow_queue_backend == "inprocess"
    assert settings.redis_url is None


def test_redis_backend_requires_redis_url() -> None:
    with pytest.raises(
        ValueError,
        match="redis_url is required",
    ):
        Settings(workflow_queue_backend="redis")


def test_production_requires_redis_workflow_queue() -> None:
    with pytest.raises(
        ValueError,
        match="Redis workflow queue backend is required",
    ):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://user:password@db/app",
        )


def test_production_redis_backend_requires_redis_url() -> None:
    with pytest.raises(
        ValueError,
        match="redis_url is required",
    ):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://user:password@db/app",
            workflow_queue_backend="redis",
        )


def test_production_redis_backend_accepts_redis_url() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://user:password@db/app",
        workflow_queue_backend="redis",
        redis_url="redis://redis:6379/0",
    )

    assert settings.workflow_queue_backend == "redis"
    assert settings.redis_url == "redis://redis:6379/0"
