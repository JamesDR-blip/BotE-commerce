"""Domain contracts for organization quotas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QuotaDimension(str, Enum):
    """Supported organization quota dimensions."""

    STORAGE_BYTES = "STORAGE_BYTES"
    DATASET_COUNT = "DATASET_COUNT"
    WORKFLOW_EXECUTION_COUNT = "WORKFLOW_EXECUTION_COUNT"


@dataclass(frozen=True)
class OrganizationQuota:
    """An organization-scoped hard quota."""

    organization_id: str
    dimension: QuotaDimension
    limit: int

    def __post_init__(self) -> None:
        if not self.organization_id.strip():
            raise ValueError("organization_id must not be blank")
        if self.limit < 0:
            raise ValueError("limit must be non-negative")


@dataclass(frozen=True)
class QuotaDecision:
    """Result of evaluating a quota before a governed mutation."""

    allowed: bool
    dimension: QuotaDimension
    current_usage: int
    requested_usage: int
    limit: int
    reason: str
