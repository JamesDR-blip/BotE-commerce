from __future__ import annotations

import pytest
from pydantic import ValidationError

from configs.settings import Settings
from worker import create_workflow_consumer


def test_create_workflow_consumer_requires_redis_backend() -> None:
    settings = Settings(
        environment="test",
        workflow_queue_backend="inprocess",
    )

    with pytest.raises(
        ValueError,
        match="workflow_queue_backend='redis'",
    ):
        create_workflow_consumer(settings)


def test_settings_requires_redis_url_for_redis_backend() -> None:
    with pytest.raises(
        ValidationError,
        match="redis_url is required when the workflow queue backend is Redis",
    ):
        Settings(
            environment="test",
            workflow_queue_backend="redis",
            redis_url=None,
        )


def test_create_workflow_consumer_wires_existing_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        workflow_queue_backend="redis",
        redis_url="redis://localhost:6379/0",
        redis_stream_name="test-workflow-stream",
        redis_consumer_group="test-workers",
    )

    class FakeWorker:
        def run(self, execution_id: str) -> None:
            del execution_id

    class FakeContainer:
        workflow_worker = FakeWorker()

    captured: dict[str, object] = {}

    def fake_build_container(received_settings: Settings) -> FakeContainer:
        assert received_settings is settings
        return FakeContainer()

    class FakeConsumer:
        def __init__(
            self,
            *,
            redis_url: str,
            stream_name: str,
            consumer_group: str,
            worker,
        ) -> None:
            captured["redis_url"] = redis_url
            captured["stream_name"] = stream_name
            captured["consumer_group"] = consumer_group
            captured["worker"] = worker

    monkeypatch.setattr("worker.build_container", fake_build_container)
    monkeypatch.setattr(
        "worker.RedisWorkflowExecutionConsumer",
        FakeConsumer,
    )

    consumer = create_workflow_consumer(settings)

    assert isinstance(consumer, FakeConsumer)
    assert captured == {
        "redis_url": "redis://localhost:6379/0",
        "stream_name": "test-workflow-stream",
        "consumer_group": "test-workers",
        "worker": FakeContainer.workflow_worker.run,
    }
