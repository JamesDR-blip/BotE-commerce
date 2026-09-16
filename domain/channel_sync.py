"""Domain contracts for multi-channel product synchronization.

This module is framework independent. It contains deterministic sync state,
canonical product contracts, channel mappings, and connector ports.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol


class ChannelType(str, Enum):
    SHOPIFY = "shopify"
    AMAZON_SP_API = "amazon_sp_api"
    TIKTOK_SHOP = "tiktok_shop"
    SHOPEE = "shopee"
    LAZADA = "lazada"


class SyncJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncAttemptStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SyncTransitionError(ValueError):
    """Raised when a sync aggregate receives an invalid state transition."""


_ALLOWED_JOB_TRANSITIONS: dict[SyncJobStatus, frozenset[SyncJobStatus]] = {
    SyncJobStatus.QUEUED: frozenset({SyncJobStatus.RUNNING, SyncJobStatus.CANCELLED}),
    SyncJobStatus.RUNNING: frozenset(
        {
            SyncJobStatus.SUCCEEDED,
            SyncJobStatus.FAILED,
            SyncJobStatus.CANCELLED,
        }
    ),
    SyncJobStatus.SUCCEEDED: frozenset(),
    SyncJobStatus.FAILED: frozenset(),
    SyncJobStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class CanonicalProduct:
    """Deterministic canonical product representation used for channel export."""

    product_id: str
    title: str
    sku: str = ""
    brand: str = ""
    price: str = ""
    attributes: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            raise ValueError("product_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if self.attributes is None:
            object.__setattr__(self, "attributes", {})


@dataclass(frozen=True)
class ChannelMapping:
    """Mapping between one canonical product and one external channel listing."""

    canonical_product_id: str
    channel: ChannelType
    external_product_id: str = ""
    last_synced_hash: str = ""
    active: bool = True

    def __post_init__(self) -> None:
        if not self.canonical_product_id.strip():
            raise ValueError("canonical_product_id is required")


@dataclass(frozen=True)
class ConnectorRequest:
    """Validated request passed from application to a channel connector."""

    product: CanonicalProduct
    mapping: ChannelMapping | None
    operation: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if self.operation not in {"create", "update", "noop"}:
            raise ValueError(f"unsupported connector operation: {self.operation}")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key is required")


@dataclass(frozen=True)
class ConnectorResult:
    """Normalized result returned by a channel connector."""

    success: bool
    external_product_id: str = ""
    remote_hash: str = ""
    message: str = ""
    retryable: bool = False

    def __post_init__(self) -> None:
        if self.success and not self.external_product_id.strip():
            raise ValueError(
                "successful connector result requires external_product_id"
            )


class Connector(Protocol):
    """Port implemented by infrastructure-specific channel connectors."""

    @property
    def channel(self) -> ChannelType:
        ...

    def sync_product(self, request: ConnectorRequest) -> ConnectorResult:
        ...


@dataclass(frozen=True)
class SyncJob:
    """Aggregate representing one idempotent channel synchronization request."""

    id: str
    workspace_id: str
    dataset_id: str
    channel_id: str
    idempotency_key: str
    status: SyncJobStatus = SyncJobStatus.QUEUED
    error: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("id", self.id),
            ("workspace_id", self.workspace_id),
            ("dataset_id", self.dataset_id),
            ("channel_id", self.channel_id),
            ("idempotency_key", self.idempotency_key),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} is required")

    def transition(self, target: SyncJobStatus, error: str | None = None) -> "SyncJob":
        allowed = _ALLOWED_JOB_TRANSITIONS[self.status]
        if target not in allowed:
            raise SyncTransitionError(
                f"invalid sync job transition: {self.status.value} -> {target.value}"
            )

        if target == SyncJobStatus.FAILED and not (error or "").strip():
            raise ValueError("failed sync job requires an error")

        return SyncJob(
            id=self.id,
            workspace_id=self.workspace_id,
            dataset_id=self.dataset_id,
            channel_id=self.channel_id,
            idempotency_key=self.idempotency_key,
            status=target,
            error=error,
        )


@dataclass(frozen=True)
class SyncAttempt:
    """One bounded connector attempt belonging to a sync job."""

    id: str
    sync_job_id: str
    attempt_number: int
    status: SyncAttemptStatus
    request_hash: str
    external_product_id: str = ""
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.sync_job_id.strip():
            raise ValueError("sync_job_id is required")
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be >= 1")
        if not self.request_hash.strip():
            raise ValueError("request_hash is required")
        if self.status == SyncAttemptStatus.FAILED and not (self.error or "").strip():
            raise ValueError("failed sync attempt requires an error")

@dataclass(frozen=True)
class Channel:
    """Workspace-owned channel connection metadata.

    Credentials are intentionally excluded from this domain contract.
    Encrypted credential material remains an infrastructure persistence concern.
    """
    id: str
    workspace_id: str
    channel: ChannelType
    name: str
    enabled: bool = True

    def __post_init__(self) -> None:
        for field_name, value in (
            ("id", self.id),
            ("workspace_id", self.workspace_id),
            ("name", self.name),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} is required")
