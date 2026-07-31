"""Repository for persisted application users."""
from __future__ import annotations

from typing import Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import UserRecord


class UserRepository:
    def __init__(self, sessions: Callable[[], Session]) -> None:
        self._sessions = sessions

    def create(self, email: str, display_name: str | None = None) -> UserRecord:
        user = UserRecord(id=str(uuid4()), email=email, display_name=display_name)
        with self._sessions() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get(self, user_id: str) -> UserRecord | None:
        with self._sessions() as session:
            return session.get(UserRecord, user_id)

    def get_by_email(self, email: str) -> UserRecord | None:
        with self._sessions() as session:
            return session.scalar(select(UserRecord).where(UserRecord.email == email))
