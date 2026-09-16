"""Repository for persisted canonical-product channel mappings."""

from __future__ import annotations

from typing import Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ChannelMappingRecord, ChannelRecord, WorkspaceRecord
from domain.channel_sync import ChannelMapping, ChannelType


class ChannelMappingRepository:
    """Persist workspace-owned mappings between canonical products and channels."""

    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_domain(record: ChannelMappingRecord) -> ChannelMapping:
        return ChannelMapping(
            canonical_product_id=record.canonical_product_id,
            channel=ChannelType(record.channel_type),
            external_product_id=record.external_product_id,
            last_synced_hash=record.last_synced_hash,
            active=record.active,
        )

    def get_for_owner(
        self,
        *,
        channel_id: str,
        canonical_product_id: str,
        owner_id: str,
    ) -> ChannelMapping | None:
        with self._sessions() as session:
            record = session.scalar(
                select(ChannelMappingRecord)
                .join(
                    ChannelRecord,
                    ChannelMappingRecord.channel_id == ChannelRecord.id,
                )
                .join(
                    WorkspaceRecord,
                    ChannelRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChannelMappingRecord.channel_id == channel_id,
                    ChannelMappingRecord.canonical_product_id
                    == canonical_product_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if record is None:
                return None

            return self._to_domain(record)

    def upsert(
        self,
        *,
        channel_id: str,
        mapping: ChannelMapping,
    ) -> ChannelMapping:
        with self._sessions() as session:
            record = session.scalar(
                select(ChannelMappingRecord).where(
                    ChannelMappingRecord.channel_id == channel_id,
                    ChannelMappingRecord.canonical_product_id
                    == mapping.canonical_product_id,
                )
            )

            if record is None:
                record = ChannelMappingRecord(
                    id=str(uuid4()),
                    channel_id=channel_id,
                    canonical_product_id=mapping.canonical_product_id,
                    channel_type=mapping.channel.value,
                    external_product_id=mapping.external_product_id,
                    last_synced_hash=mapping.last_synced_hash,
                    active=mapping.active,
                )
                session.add(record)
            else:
                record.channel_type = mapping.channel.value
                record.external_product_id = mapping.external_product_id
                record.last_synced_hash = mapping.last_synced_hash
                record.active = mapping.active

            session.commit()
            session.refresh(record)

            return self._to_domain(record)

