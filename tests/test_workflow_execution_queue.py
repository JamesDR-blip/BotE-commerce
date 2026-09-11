from __future__ import annotations

import threading
import time

from infrastructure.queue.workflow_execution_queue import (
    InProcessWorkflowExecutionQueue,
)


def test_in_process_queue_dispatch_is_background() -> None:
    started = threading.Event()
    release = threading.Event()
    received: list[str] = []

    def worker(execution_id: str) -> None:
        received.append(execution_id)
        started.set()
        release.wait(timeout=2)

    queue = InProcessWorkflowExecutionQueue(
        worker=worker,
    )

    try:
        queue.dispatch("execution-1")

        assert started.wait(timeout=2)
        assert received == ["execution-1"]
    finally:
        release.set()
        queue.stop()


def test_in_process_queue_processes_execution_ids_fifo() -> None:
    received: list[str] = []
    done = threading.Event()

    def worker(execution_id: str) -> None:
        received.append(execution_id)
        if len(received) == 3:
            done.set()

    queue = InProcessWorkflowExecutionQueue(
        worker=worker,
    )

    try:
        queue.dispatch("execution-1")
        queue.dispatch("execution-2")
        queue.dispatch("execution-3")

        assert done.wait(timeout=2)
        assert received == [
            "execution-1",
            "execution-2",
            "execution-3",
        ]
    finally:
        queue.stop()
