"""Repository for workspace-owned channel persistence."""

from __future__ import annotations

from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from application.channels.credential_cipher import CredentialCipher
from database.models import ChannelRecord, WorkspaceRecord
from domain.channel_sync import Channel, ChannelType


class ChannelRepository:
    """Persist channel metadata while protecting credentials at rest."""

    def __init__(
        self,
        sessions: Callable[[], Session],
        credential_cipher: CredentialCipher,
    ) -> None:
        self._sessions = sessions
        self._credential_cipher = credential_cipher

    @staticmethod
    def _to_domain(record: ChannelRecord) -> Channel:
        return Channel(
            id=record.id,
            workspace_id=record.workspace_id,
            channel=ChannelType(record.channel_type),
            name=record.name,
            enabled=record.enabled,
        )

    def create(
        self,
        *,
        channel: Channel,
        credentials: str,
    ) -> Channel:
        if not credentials:
            raise ValueError("channel credentials are required")

        encrypted = self._credential_cipher.encrypt(credentials)

        with self._sessions() as session:
            record = ChannelRecord(
                id=channel.id,
                workspace_id=channel.workspace_id,
                channel_type=channel.channel.value,
                name=channel.name,
                credentials_encrypted=encrypted,
                enabled=channel.enabled,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return self._to_domain(record)

    def get(
        self,
        channel_id: str,
    ) -> Channel | None:
        with self._sessions() as session:
            record = session.get(ChannelRecord, channel_id)
            if record is None:
                return None
            return self._to_domain(record)

    def get_for_owner(
        self,
        *,
        channel_id: str,
        owner_id: str,
    ) -> Channel | None:
        with self._sessions() as session:
            record = session.scalar(
                select(ChannelRecord)
                .join(
                    WorkspaceRecord,
                    ChannelRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChannelRecord.id == channel_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if record is None:
                return None

            return self._to_domain(record)

    def list_for_owner(
        self,
        *,
        workspace_id: str,
        owner_id: str,
    ) -> list[Channel]:
        with self._sessions() as session:
            records = session.scalars(
                select(ChannelRecord)
                .join(
                    WorkspaceRecord,
                    ChannelRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChannelRecord.workspace_id == workspace_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
                .order_by(ChannelRecord.created_at, ChannelRecord.id)
            )

            return [self._to_domain(record) for record in records]

    def get_credentials_for_owner(
        self,
        *,
        channel_id: str,
        owner_id: str,
    ) -> str | None:
        """Decrypt credentials only after workspace ownership is verified."""
        with self._sessions() as session:
            encrypted = session.scalar(
                select(ChannelRecord.credentials_encrypted)
                .join(
                    WorkspaceRecord,
                    ChannelRecord.workspace_id == WorkspaceRecord.id,
                )
                .where(
                    ChannelRecord.id == channel_id,
                    WorkspaceRecord.owner_id == owner_id,
                )
            )

            if encrypted is None:
                return None

            return self._credential_cipher.decrypt(encrypted)
