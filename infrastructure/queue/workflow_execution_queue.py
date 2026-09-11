"""Minimal in-process background queue for workflow execution IDs."""

from __future__ import annotations

from collections.abc import Callable
from queue import Queue
from threading import Event, Thread


class InProcessWorkflowExecutionQueue:
    """FIFO background worker queue.

    Only persisted execution IDs cross the queue boundary.
    """

    def __init__(
        self,
        *,
        worker: Callable[[str], None],
        worker_name: str = "workflow-execution-worker",
    ) -> None:
        self._worker = worker
        self._items: Queue[str | None] = Queue()
        self._stopped = Event()
        self._thread = Thread(
            target=self._run,
            name=worker_name,
            daemon=True,
        )
        self._thread.start()

    def dispatch(self, execution_id: str) -> None:
        if self._stopped.is_set():
            raise RuntimeError("Workflow execution queue is stopped")

        self._items.put(execution_id)

    def stop(self) -> None:
        if self._stopped.is_set():
            return

        self._stopped.set()
        self._items.put(None)

        if self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while True:
            execution_id = self._items.get()

            try:
                if execution_id is None:
                    return

                try:
                    self._worker(execution_id)
                except Exception:
                    # A worker-level exception must not terminate the
                    # background thread. The execution worker is responsible
                    # for persisting execution failure state.
                    continue
            finally:
                self._items.task_done()
