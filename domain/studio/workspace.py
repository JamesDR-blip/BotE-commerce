"""Workspace domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Workspace:
    """
    Top-level container for AI Studio resources.
    """

    id: str
    name: str
    created_at: datetime | None = None