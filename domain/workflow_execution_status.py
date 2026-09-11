from enum import Enum


class WorkflowExecutionStatus(str, Enum):

    CREATED = "CREATED"

    QUEUED = "QUEUED"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"
