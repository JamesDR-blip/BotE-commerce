"""Project domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Project:
    """
    Ecommerce AI Studio project.

    A project belongs to a workspace and owns datasets/workflows.
    """

    id: str
    workspace_id: str
    name: str
    description: str | None = None
    created_at: datetime | None = None