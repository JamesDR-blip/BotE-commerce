"""Production worker entrypoint for Redis-backed workflow executions."""

from __future__ import annotations

from configs.settings import Settings
from infrastructure.queue.redis_workflow_execution_queue import (
    RedisWorkflowExecutionConsumer,
)
from services.container import build_container


def create_workflow_consumer(
    settings: Settings | None = None,
) -> RedisWorkflowExecutionConsumer:
    """Build the Redis workflow consumer from application configuration."""
    settings = settings or Settings()

    if settings.workflow_queue_backend != "redis":
        raise ValueError(
            "Redis workflow worker requires workflow_queue_backend='redis'"
        )

    if not settings.redis_url:
        raise ValueError("redis_url is required for the Redis workflow worker")

    container = build_container(settings)

    return RedisWorkflowExecutionConsumer(
        redis_url=settings.redis_url,
        stream_name=settings.redis_stream_name,
        consumer_group=settings.redis_consumer_group,
        worker=container.workflow_worker.run,
    )


def main() -> None:
    """Run the Redis workflow consumer until the process is stopped."""
    consumer = create_workflow_consumer()
    consumer.run_forever()


if __name__ == "__main__":
    main()
