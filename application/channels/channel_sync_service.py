"""Application service for idempotent multi-channel catalog synchronization."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from uuid import uuid4

from application.audit.audit_service import AuditService
from application.channels.canonical_product_service import CanonicalProductService
from domain.channel_sync import (
    Channel,
    ChannelMapping,
    ChannelType,
    Connector,
    ConnectorRequest,
    SyncAttempt,
    SyncAttemptStatus,
    SyncJob,
    SyncJobStatus,
)
from domain.identity import CurrentUser
from repositories.datasets import DatasetRepository
from repositories.projects import ProjectRepository
from repositories.channel_mappings import ChannelMappingRepository
from repositories.channels import ChannelRepository
from repositories.sync_jobs import SyncAttemptRepository, SyncJobRepository


class ChannelSyncService:
    """Coordinate deterministic product projection and external channel sync."""

    def __init__(
        self,
        *,
        channels: ChannelRepository,
        mappings: ChannelMappingRepository,
        sync_jobs: SyncJobRepository,
        sync_attempts: SyncAttemptRepository,
        canonical_products: CanonicalProductService,
        datasets: DatasetRepository,
        projects: ProjectRepository,
        connector_factory: Callable[[ChannelType, str], Connector],
        audit_service: AuditService,
    ) -> None:
        self._channels = channels
        self._mappings = mappings
        self._sync_jobs = sync_jobs
        self._sync_attempts = sync_attempts
        self._canonical_products = canonical_products
        self._datasets = datasets
        self._projects = projects
        self._connector_factory = connector_factory
        self._audit = audit_service

    def sync(
        self,
        *,
        current_user: CurrentUser,
        channel_id: str,
        dataset_id: str,
        idempotency_key: str,
    ) -> SyncJob:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")

        channel = self._channels.get_for_owner(
            channel_id=channel_id,
            owner_id=current_user.user_id,
        )

        if channel is None:
            raise ValueError(f"Channel not found: {channel_id}")

        existing = self._sync_jobs.get_by_idempotency_key_for_owner(
            workspace_id=channel.workspace_id,
            owner_id=current_user.user_id,
            idempotency_key=idempotency_key,
        )

        if existing is not None:
            if (
                existing.channel_id != channel_id
                or existing.dataset_id != dataset_id
            ):
                raise ValueError(
                    "idempotency_key is already associated with a "
                    "different channel sync"
                )
            return existing

        if not channel.enabled:
            raise ValueError(f"Channel is disabled: {channel_id}")

        dataset = self._datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )
        if dataset is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        project = self._projects.get_for_owner(
            project_id=dataset.project_id,
            owner_id=current_user.user_id,
        )
        if project is None or project.workspace_id != channel.workspace_id:
            raise ValueError(f"Dataset not found: {dataset_id}")

        products = self._canonical_products.project_dataset(
            current_user=current_user,
            dataset_id=dataset_id,
        )

        job = SyncJob(
            id=str(uuid4()),
            workspace_id=channel.workspace_id,
            dataset_id=dataset_id,
            channel_id=channel_id,
            idempotency_key=idempotency_key,
        )
        job = self._sync_jobs.create(job=job)

        self._audit_event(
            current_user=current_user,
            channel=channel,
            job=job,
            action="channel.sync.started",
            metadata={"product_count": len(products)},
        )

        try:
            job = self._sync_jobs.update(
                job=job.transition(SyncJobStatus.RUNNING)
            )

            credentials = self._channels.get_credentials_for_owner(
                channel_id=channel_id,
                owner_id=current_user.user_id,
            )

            if credentials is None:
                raise ValueError(f"Channel not found: {channel_id}")

            connector = self._connector_factory(
                channel.channel,
                credentials,
            )

            failures: list[str] = []

            for index, product in enumerate(products, start=1):
                mapping = self._mappings.get_for_owner(
                    channel_id=channel_id,
                    canonical_product_id=product.product_id,
                    owner_id=current_user.user_id,
                )

                desired_hash = self._product_hash(product)

                if (
                    mapping is not None
                    and mapping.active
                    and mapping.external_product_id.strip()
                    and mapping.last_synced_hash == desired_hash
                ):
                    operation = "noop"
                elif mapping is not None and mapping.external_product_id:
                    operation = "update"
                else:
                    operation = "create"

                request = ConnectorRequest(
                    product=product,
                    mapping=mapping,
                    operation=operation,
                    idempotency_key=(
                        f"{idempotency_key}:{product.product_id}"
                    ),
                )

                try:
                    result = connector.sync_product(request)
                except Exception as exc:
                    message = self._safe_exception_message(exc)
                    result_success = False
                    result_external_id = ""
                    result_message = message
                else:
                    result_success = result.success
                    result_external_id = result.external_product_id
                    result_message = result.message

                attempt = SyncAttempt(
                    id=str(uuid4()),
                    sync_job_id=job.id,
                    attempt_number=index,
                    status=(
                        SyncAttemptStatus.SUCCEEDED
                        if result_success
                        else SyncAttemptStatus.FAILED
                    ),
                    request_hash=desired_hash,
                    external_product_id=result_external_id,
                    error=None if result_success else result_message,
                )
                self._sync_attempts.create(attempt=attempt)

                if not result_success:
                    failures.append(
                        f"{product.product_id}: {result_message}"
                    )
                    continue

                self._mappings.upsert(
                    channel_id=channel_id,
                    mapping=ChannelMapping(
                        canonical_product_id=product.product_id,
                        channel=channel.channel,
                        external_product_id=result_external_id,
                        last_synced_hash=desired_hash,
                        active=True,
                    ),
                )

            if failures:
                error = "; ".join(failures[:5])
                if len(failures) > 5:
                    error += f"; {len(failures) - 5} additional failures"

                job = self._sync_jobs.update(
                    job=job.transition(
                        SyncJobStatus.FAILED,
                        error=error,
                    )
                )

                self._audit_event(
                    current_user=current_user,
                    channel=channel,
                    job=job,
                    action="channel.sync.failed",
                    metadata={
                        "failure_count": len(failures),
                        "product_count": len(products),
                    },
                )
                return job

            job = self._sync_jobs.update(
                job=job.transition(SyncJobStatus.SUCCEEDED)
            )

            self._audit_event(
                current_user=current_user,
                channel=channel,
                job=job,
                action="channel.sync.succeeded",
                metadata={"product_count": len(products)},
            )

            return job

        except Exception as exc:
            error = self._safe_exception_message(exc)

            current = self._sync_jobs.get(job.id) or job

            if current.status is SyncJobStatus.RUNNING:
                job = self._sync_jobs.update(
                    job=current.transition(
                        SyncJobStatus.FAILED,
                        error=error,
                    )
                )
            else:
                raise

            self._audit_event(
                current_user=current_user,
                channel=channel,
                job=job,
                action="channel.sync.failed",
                metadata={"error": error},
            )

            return job

    @staticmethod
    def _product_hash(product: object) -> str:
        payload = {
            "product_id": product.product_id,
            "title": product.title,
            "sku": product.sku,
            "brand": product.brand,
            "price": product.price,
            "attributes": product.attributes,
        }

        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _audit_event(
        self,
        *,
        current_user: CurrentUser,
        channel: Channel,
        job: SyncJob,
        action: str,
        metadata: dict[str, object],
    ) -> None:
        self._audit.record(
            workspace_id=channel.workspace_id,
            actor_id=current_user.user_id,
            action=action,
            resource_type="sync_job",
            resource_id=job.id,
            metadata={
                "channel_id": channel.id,
                "channel_type": channel.channel.value,
                "dataset_id": job.dataset_id,
                "idempotency_key": job.idempotency_key,
                **metadata,
            },
        )

    @staticmethod
    def _safe_exception_message(exc: Exception) -> str:
        message = str(exc).strip()

        if not message:
            return exc.__class__.__name__

        return message[:500]

