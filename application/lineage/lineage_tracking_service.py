"""Application service for recording data lineage."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

from domain.lineage import DataLineageEvent
from repositories.data_lineage_events import DataLineageEventRepository


class LineageTrackingService:
    """Creates immutable lineage events without owning infrastructure concerns."""

    def __init__(
        self,
        repository: DataLineageEventRepository,
    ) -> None:
        self._repository = repository

    def record(
        self,
        *,
        dataset_id: str,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        capability_id: str,
        capability_version: str,
        event_type: str,
        input_refs: dict[str, Any] | None = None,
        output_refs: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> DataLineageEvent:
        event = DataLineageEvent(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            capability_id=capability_id,
            capability_version=capability_version,
            event_type=event_type,
            input_refs=dict(input_refs or {}),
            output_refs=dict(output_refs or {}),
            created_at=created_at or datetime.now(timezone.utc),
        )

        self._repository.add(event)
        return event

    def record_in_transaction(
        self,
        session,
        *,
        dataset_id: str,
        execution_id: str,
        workflow_id: str,
        workflow_version: str,
        capability_id: str,
        capability_version: str,
        event_type: str,
        input_refs: dict[str, Any] | None = None,
        output_refs: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> DataLineageEvent:
        event = DataLineageEvent(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            capability_id=capability_id,
            capability_version=capability_version,
            event_type=event_type,
            input_refs=dict(input_refs or {}),
            output_refs=dict(output_refs or {}),
            created_at=created_at or datetime.now(timezone.utc),
        )

        self._repository.add_in_transaction(
            session,
            event,
        )
        return event

    def list_for_dataset(
        self,
        *,
        dataset_id: str,
        owner_id: str,
    ) -> list[DataLineageEvent]:
        return self._repository.list_for_dataset_owner(
            dataset_id=dataset_id,
            owner_id=owner_id,
        )
