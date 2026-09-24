from __future__ import annotations

import pytest

from infrastructure.queue.redis_workflow_execution_queue import (
    RedisWorkflowExecutionConsumer,
    RedisWorkflowExecutionQueue,
)


class FakeRedis:
    def __init__(self) -> None:
        self.entries: list[tuple[str, dict[str, str]]] = []
        self.acks: list[str] = []
        self.created_groups: list[str] = []

    def xadd(
        self,
        stream_name: str,
        payload: dict[str, str],
    ) -> str:
        self.entries.append(("1-0", payload))
        return "1-0"

    def xgroup_create(
        self,
        *,
        name: str,
        groupname: str,
        id: str,
        mkstream: bool,
    ) -> None:
        self.created_groups.append(groupname)

    def xack(
        self,
        stream_name: str,
        groupname: str,
        message_id: str,
    ) -> int:
        self.acks.append(message_id)
        return 1


def make_queue(redis: FakeRedis) -> RedisWorkflowExecutionQueue:
    queue = RedisWorkflowExecutionQueue.__new__(RedisWorkflowExecutionQueue)
    queue._redis = redis
    queue._stream_name = "workflow-executions"
    return queue


def make_consumer(
    redis: FakeRedis,
    worker,
) -> RedisWorkflowExecutionConsumer:
    consumer = RedisWorkflowExecutionConsumer.__new__(RedisWorkflowExecutionConsumer)
    consumer._redis = redis
    consumer._stream_name = "workflow-executions"
    consumer._consumer_group = "workflow-workers"
    consumer._consumer_name = "test-worker"
    consumer._worker = worker
    consumer._block_ms = 1
    consumer._claim_idle_ms = 1
    return consumer


def test_redis_queue_dispatches_only_execution_id() -> None:
    redis = FakeRedis()
    queue = make_queue(redis)

    queue.dispatch("execution-123")

    assert redis.entries == [
        (
            "1-0",
            {"execution_id": "execution-123"},
        )
    ]


def test_consumer_creates_consumer_group() -> None:
    redis = FakeRedis()
    consumer = make_consumer(redis, lambda _: None)

    consumer.ensure_group()

    assert redis.created_groups == ["workflow-workers"]


def test_consumer_acks_after_worker_returns() -> None:
    redis = FakeRedis()
    received: list[str] = []

    consumer = make_consumer(
        redis,
        received.append,
    )

    consumer._process_message(
        message_id="1-0",
        payload={"execution_id": "execution-123"},
    )

    assert received == ["execution-123"]
    assert redis.acks == ["1-0"]


def test_consumer_does_not_ack_when_worker_raises() -> None:
    redis = FakeRedis()

    def failing_worker(_: str) -> None:
        raise RuntimeError("worker crashed")

    consumer = make_consumer(redis, failing_worker)

    with pytest.raises(RuntimeError, match="worker crashed"):
        consumer._process_message(
            message_id="1-0",
            payload={"execution_id": "execution-123"},
        )

    assert redis.acks == []


def test_consumer_acks_malformed_message_without_execution_id() -> None:
    redis = FakeRedis()
    consumer = make_consumer(redis, lambda _: None)

    consumer._process_message(
        message_id="1-0",
        payload={},
    )

    assert redis.acks == ["1-0"]
