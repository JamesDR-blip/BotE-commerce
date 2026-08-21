from datetime import datetime

from database.models import make_session_factory

from repositories.capability_execution_traces import (
    CapabilityExecutionTraceRepository,
)

from domain.execution_trace import CapabilityExecutionRecord
from domain.execution_status import ExecutionStatus

def test_create_trace_records():

    repo = CapabilityExecutionTraceRepository(
        make_session_factory("sqlite://")
    )

    record = CapabilityExecutionRecord(
        capability_id="data.validate",
        capability_version="1.0",
        status=ExecutionStatus.COMPLETED,
        inputs={},
        outputs={"ok": True},
        started_at=datetime.now(),
        finished_at=datetime.now(),
    )

    repo.create_many(
        execution_id="exec-1",
        records=[record],
    )