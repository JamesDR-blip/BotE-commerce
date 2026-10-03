"""Redis-backed workflow execution transport.

The Redis queue transports persisted workflow execution IDs only.
Execution state remains authoritative in the database.
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from threading import Event, Thread

from redis import Redis
from redis.exceptions import ResponseError


class RedisWorkflowExecutionQueue:
    """Producer-side Redis Streams adapter for workflow execution IDs."""

    def __init__(
        self,
        *,
        redis_url: str,
        stream_name: str,
    ) -> None:
        self._redis = Redis.from_url(
            redis_url,
            decode_responses=True,
        )
        self._stream_name = stream_name

    def dispatch(self, execution_id: str) -> None:
        self._redis.xadd(
            self._stream_name,
            {"execution_id": execution_id},
        )

    def ping(self) -> bool:
        return bool(self._redis.ping())


class RedisWorkflowExecutionConsumer:
    """Redis Streams consumer that delegates execution to the existing worker."""

    def __init__(
        self,
        *,
        redis_url: str,
        stream_name: str,
        consumer_group: str,
        worker: Callable[[str], None],
        recovery_worker: Callable[[str], None] | None = None,
        consumer_name: str | None = None,
        block_ms: int = 5000,
        claim_idle_ms: int = 60000,
    ) -> None:
        self._redis = Redis.from_url(
            redis_url,
            decode_responses=True,
        )
        self._stream_name = stream_name
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name or f"{socket.gethostname()}-{id(self)}"
        self._worker = worker
        self._recovery_worker = recovery_worker
        self._block_ms = block_ms
        self._claim_idle_ms = claim_idle_ms
        self._stop_event = Event()

    def ensure_group(self) -> None:
        try:
            self._redis.xgroup_create(
                name=self._stream_name,
                groupname=self._consumer_group,
                id="0",
                mkstream=True,
            )
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def stop(self) -> None:
        self._stop_event.set()

    def run_forever(self) -> None:
        self.ensure_group()
        self._recover_pending()

        while not self._stop_event.is_set():
            messages = self._redis.xreadgroup(
                groupname=self._consumer_group,
                consumername=self._consumer_name,
                streams={self._stream_name: ">"},
                count=1,
                block=self._block_ms,
            )

            for _, entries in messages:
                for message_id, payload in entries:
                    self._process_message(
                        message_id=message_id,
                        payload=payload,
                    )

    def _recover_pending(self) -> None:
        cursor = "0-0"

        while not self._stop_event.is_set():
            result = self._redis.xautoclaim(
                name=self._stream_name,
                groupname=self._consumer_group,
                consumername=self._consumer_name,
                min_idle_time=self._claim_idle_ms,
                start_id=cursor,
                count=10,
            )

            cursor = result[0]
            entries = result[1]

            for message_id, payload in entries:
                self._process_message(
                    message_id=message_id,
                    payload=payload,
                    recovered=True,
                )

            if not entries:
                return

    def _process_message(
        self,
        *,
        message_id: str,
        payload: dict[str, str],
        recovered: bool = False,
    ) -> None:
        execution_id = payload.get("execution_id")

        if not execution_id:
            self._redis.xack(
                self._stream_name,
                self._consumer_group,
                message_id,
            )
            return

        heartbeat_stop = Event()
        heartbeat = Thread(
            target=self._keep_delivery_alive,
            args=(message_id, heartbeat_stop),
            daemon=True,
        )
        heartbeat.start()

        try:
            if recovered and self._recovery_worker is not None:
                self._recovery_worker(execution_id)
            else:
                self._worker(execution_id)
        finally:
            heartbeat_stop.set()
            heartbeat.join(timeout=1)

        self._redis.xack(
            self._stream_name,
            self._consumer_group,
            message_id,
        )

    def _keep_delivery_alive(
        self,
        message_id: str,
        stop_event: Event,
    ) -> None:
        """Renew this consumer's pending-message lease during execution."""
        interval = max(
            0.1,
            min(10.0, self._claim_idle_ms / 3000),
        )

        while not stop_event.wait(interval):
            pending = self._redis.xpending_range(
                self._stream_name,
                self._consumer_group,
                min=message_id,
                max=message_id,
                count=1,
                consumername=self._consumer_name,
            )
            if not pending:
                return

            # XCLAIM uses the idle threshold as a compare-and-swap: once a
            # different consumer owns and renews the message, this consumer
            # cannot steal it back.
            self._redis.xclaim(
                name=self._stream_name,
                groupname=self._consumer_group,
                consumername=self._consumer_name,
                min_idle_time=self._claim_idle_ms,
                message_ids=[message_id],
                idle=0,
            )
