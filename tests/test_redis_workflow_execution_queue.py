from __future__ import annotations

import pytest
from threading import Event, Thread
from time import sleep

from infrastructure.queue.redis_workflow_execution_queue import (
    RedisWorkflowExecutionConsumer,
    RedisWorkflowExecutionQueue,
)
from database.models import make_session_factory
from execution.workflow.engine import WorkflowExecutionWorker
from repositories.workflow_executions import WorkflowExecutionRepository


class FakeRedis:
    def __init__(self) -> None:
        self.entries: list[tuple[str, dict[str, str]]] = []
        self.acks: list[str] = []
        self.created_groups: list[str] = []
        self.lease_claims: list[dict[str, object]] = []

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

    def xpending_range(
        self,
        stream_name,
        groupname,
        *,
        min,
        max,
        count,
        consumername,
    ):
        return [{"consumer": consumername}]

    def xclaim(self, **kwargs):
        self.lease_claims.append(kwargs)
        return []


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

    # Keep a long-running pending execution visible to Redis's idle-message
    # recovery without allowing this consumer to steal another owner's entry.
    stop = Event()
    heartbeat = Thread(
        target=consumer._keep_delivery_alive,
        args=("1-0", stop),
    )
    heartbeat.start()
    try:
        sleep(0.15)
        assert redis.lease_claims
        claim = redis.lease_claims[0]
        assert claim["consumername"] == "test-worker"
        assert claim["min_idle_time"] == 1
        assert claim["idle"] == 0
    finally:
        stop.set()
        heartbeat.join(timeout=1)

    consumer._process_message(
        message_id="1-0",
        payload={"execution_id": "execution-123"},
    )

    assert received == ["execution-123"]
    assert redis.acks == ["1-0"]

    # Reproduce process death after the durable claim, then deliver the
    # pending message through the recovery callback on the next consumer.
    sessions = make_session_factory("sqlite://")
    executions = WorkflowExecutionRepository(sessions)
    executions.create(
        execution_id="exec-crash-window",
        workflow_id="workflow-1",
        workflow_version="1.0",
        status="QUEUED",
        inputs_json="{}",
    )
    assert executions.claim_running("exec-crash-window") is not None
    worker = WorkflowExecutionWorker(
        executions=executions,
        workflow_engine=object(),
    )
    consumer._worker = worker.run
    consumer._recovery_worker = worker.recover
    consumer._process_message(
        message_id="2-0",
        payload={"execution_id": "exec-crash-window"},
        recovered=True,
    )
    crashed_execution = executions.get("exec-crash-window")
    assert crashed_execution is not None
    assert crashed_execution.status == "FAILED"
    assert "lease expired" in crashed_execution.error
    assert redis.acks == ["1-0", "2-0"]

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
