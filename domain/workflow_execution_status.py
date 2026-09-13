from enum import Enum


class WorkflowExecutionStatus(str, Enum):

    CREATED = "CREATED"

    QUEUED = "QUEUED"

    PENDING_APPROVAL = "PENDING_APPROVAL"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"


