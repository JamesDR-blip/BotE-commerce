from enum import Enum


class WorkflowExecutionStatus(str, Enum):

    CREATED = "CREATED"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"