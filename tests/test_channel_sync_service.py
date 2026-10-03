from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from application.channels.channel_sync_service import ChannelSyncService
from domain.channel_sync import (
    CanonicalProduct,
    Channel,
    ChannelMapping,
    ChannelType,
    ConnectorResult,
    SyncAttemptStatus,
    SyncJob,
    SyncJobStatus,
)
from domain.identity import CurrentUser


def make_service():
    channels = MagicMock()
    mappings = MagicMock()
    sync_jobs = MagicMock()
    sync_attempts = MagicMock()
    canonical_products = MagicMock()
    datasets = MagicMock()
    projects = MagicMock()
    connector = MagicMock()
    audit = MagicMock()

    factory = MagicMock(return_value=connector)

    service = ChannelSyncService(
        channels=channels,
        mappings=mappings,
        sync_jobs=sync_jobs,
        sync_attempts=sync_attempts,
        canonical_products=canonical_products,
        datasets=datasets,
        projects=projects,
        connector_factory=factory,
        audit_service=audit,
    )

    return (
        service,
        channels,
        mappings,
        sync_jobs,
        sync_attempts,
        canonical_products,
        datasets,
        projects,
        connector,
        audit,
        factory,
    )


def make_channel() -> Channel:
    return Channel(
        id="channel-1",
        workspace_id="workspace-1",
        channel=ChannelType.SHOPIFY,
        name="Shopify Main",
        enabled=True,
    )


def make_product(product_id: str = "sku-1") -> CanonicalProduct:
    return CanonicalProduct(
        product_id=product_id,
        title=f"Product {product_id}",
        sku=product_id,
        brand="Brand",
        price="10.00",
        attributes={"color": "black"},
    )


def make_dataset():
    return SimpleNamespace(
        id="dataset-1",
        project_id="project-1",
    )


def make_project():
    return SimpleNamespace(
        id="project-1",
        workspace_id="workspace-1",
    )


def make_created_job() -> SyncJob:
    return SyncJob(
        id="job-1",
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        channel_id="channel-1",
        idempotency_key="idem-1",
    )


def test_get_sync_job_uses_current_owner_and_returns_repository_result():
    service_parts = make_service()
    service, _, _, sync_jobs, *_ = service_parts
    current_user = CurrentUser(user_id="owner-1")
    job = make_created_job()
    sync_jobs.get_for_owner.side_effect = [job, None]

    result = service.get_sync_job(
        sync_job_id="job-1",
        current_user=current_user,
    )
    missing = service.get_sync_job(
        sync_job_id="missing-job",
        current_user=current_user,
    )

    assert result is job
    assert missing is None
    assert sync_jobs.get_for_owner.call_args_list == [
        call(job_id="job-1", owner_id="owner-1"),
        call(job_id="missing-job", owner_id="owner-1"),
    ]


def configure_common(service_parts):
    (
        _service,
        channels,
        mappings,
        sync_jobs,
        _sync_attempts,
        canonical_products,
        datasets,
        projects,
        _connector,
        _audit,
        _factory,
    ) = service_parts

    channels.get_for_owner.return_value = make_channel()
    channels.get_credentials_for_owner.return_value = '{"access_token":"secret"}'

    sync_jobs.get_by_idempotency_key_for_owner.return_value = None
    mappings.get_for_owner.return_value = None

    datasets.get_for_owner.return_value = make_dataset()
    projects.get_for_owner.return_value = make_project()

    canonical_products.project_dataset.return_value = [make_product()]

    created = make_created_job()
    sync_jobs.create.return_value = created
    sync_jobs.update.side_effect = lambda *, job: job

    return created


def test_idempotency_returns_existing_job_without_syncing():
    parts = make_service()
    (
        service,
        channels,
        _mappings,
        sync_jobs,
        sync_attempts,
        canonical_products,
        _datasets,
        _projects,
        connector,
        audit,
        factory,
    ) = parts

    existing = SyncJob(
        id="existing-job",
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        channel_id="channel-1",
        idempotency_key="idem-1",
        status=SyncJobStatus.SUCCEEDED,
    )

    channels.get_for_owner.return_value = make_channel()
    sync_jobs.get_by_idempotency_key_for_owner.return_value = existing

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result is existing
    sync_jobs.create.assert_not_called()
    sync_jobs.update.assert_not_called()
    sync_attempts.create.assert_not_called()
    canonical_products.project_dataset.assert_not_called()
    connector.sync_product.assert_not_called()
    factory.assert_not_called()
    audit.record.assert_not_called()


def test_idempotency_key_cannot_be_reused_for_different_dataset():
    parts = make_service()
    (
        service,
        channels,
        _mappings,
        sync_jobs,
        _sync_attempts,
        _canonical_products,
        _datasets,
        _projects,
        _connector,
        _audit,
        _factory,
    ) = parts

    channels.get_for_owner.return_value = make_channel()
    sync_jobs.get_by_idempotency_key_for_owner.return_value = SyncJob(
        id="existing-job",
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        channel_id="channel-1",
        idempotency_key="idem-1",
    )

    with pytest.raises(
        ValueError,
        match="different channel sync",
    ):
        service.sync(
            current_user=CurrentUser(user_id="user-1"),
            channel_id="channel-1",
            dataset_id="dataset-2",
            idempotency_key="idem-1",
        )


def test_disabled_channel_is_rejected():
    parts = make_service()
    (
        service,
        channels,
        _mappings,
        _sync_jobs,
        _sync_attempts,
        _canonical_products,
        _datasets,
        _projects,
        _connector,
        _audit,
        _factory,
    ) = parts

    channels.get_for_owner.return_value = Channel(
        id="channel-1",
        workspace_id="workspace-1",
        channel=ChannelType.SHOPIFY,
        name="Shopify Main",
        enabled=False,
    )
    _sync_jobs.get_by_idempotency_key_for_owner.return_value = None

    with pytest.raises(
        ValueError,
        match="Channel is disabled",
    ):
        service.sync(
            current_user=CurrentUser(user_id="user-1"),
            channel_id="channel-1",
            dataset_id="dataset-1",
            idempotency_key="idem-1",
        )


def test_dataset_must_belong_to_same_workspace_as_channel():
    parts = make_service()
    (
        service,
        channels,
        _mappings,
        sync_jobs,
        _sync_attempts,
        _canonical_products,
        datasets,
        projects,
        _connector,
        _audit,
        _factory,
    ) = parts

    channels.get_for_owner.return_value = make_channel()
    sync_jobs.get_by_idempotency_key_for_owner.return_value = None
    datasets.get_for_owner.return_value = make_dataset()
    projects.get_for_owner.return_value = SimpleNamespace(
        id="project-1",
        workspace_id="different-workspace",
    )

    with pytest.raises(ValueError, match="Dataset not found"):
        service.sync(
            current_user=CurrentUser(user_id="user-1"),
            channel_id="channel-1",
            dataset_id="dataset-1",
            idempotency_key="idem-1",
        )


def test_create_sync_succeeds_and_persists_mapping_and_attempt():
    parts = make_service()
    (
        service,
        channels,
        mappings,
        sync_jobs,
        sync_attempts,
        _canonical_products,
        datasets,
        projects,
        connector,
        audit,
        factory,
    ) = parts

    configure_common(parts)

    connector.sync_product.return_value = ConnectorResult(
        success=True,
        external_product_id="shopify-product-1",
        remote_hash="remote-hash",
    )

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.SUCCEEDED

    factory.assert_called_once_with(
        ChannelType.SHOPIFY,
        '{"access_token":"secret"}',
    )

    request = connector.sync_product.call_args.args[0]
    assert request.operation == "create"
    assert request.product.product_id == "sku-1"
    assert request.idempotency_key == "idem-1:sku-1"

    attempt = sync_attempts.create.call_args.kwargs["attempt"]
    assert attempt.status is SyncAttemptStatus.SUCCEEDED
    assert attempt.external_product_id == "shopify-product-1"
    assert attempt.error is None

    mapping = mappings.upsert.call_args.kwargs["mapping"]
    assert mapping.canonical_product_id == "sku-1"
    assert mapping.channel is ChannelType.SHOPIFY
    assert mapping.external_product_id == "shopify-product-1"
    assert mapping.last_synced_hash == attempt.request_hash

    assert audit.record.call_count == 2
    assert audit.record.call_args_list[0].kwargs["action"] == (
        "channel.sync.started"
    )
    assert audit.record.call_args_list[1].kwargs["action"] == (
        "channel.sync.succeeded"
    )

    for audit_call in audit.record.call_args_list:
        metadata = audit_call.kwargs["metadata"]
        assert "secret" not in str(metadata)


def test_existing_mapping_with_same_hash_uses_noop():
    parts = make_service()
    (
        service,
        channels,
        mappings,
        sync_jobs,
        sync_attempts,
        _canonical_products,
        _datasets,
        _projects,
        connector,
        _audit,
        _factory,
    ) = parts

    configure_common(parts)

    product = make_product()
    product_hash = service._product_hash(product)

    mappings.get_for_owner.return_value = ChannelMapping(
        canonical_product_id=product.product_id,
        channel=ChannelType.SHOPIFY,
        external_product_id="shopify-product-1",
        last_synced_hash=product_hash,
        active=True,
    )

    connector.sync_product.return_value = ConnectorResult(
        success=True,
        external_product_id="shopify-product-1",
    )

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.SUCCEEDED

    request = connector.sync_product.call_args.args[0]
    assert request.operation == "noop"
    assert request.mapping is not None
    assert request.mapping.external_product_id == "shopify-product-1"

    sync_attempts.create.assert_called_once()
    mappings.upsert.assert_called_once()


def test_existing_mapping_with_changed_hash_uses_update():
    parts = make_service()
    (
        service,
        channels,
        mappings,
        _sync_jobs,
        _sync_attempts,
        _canonical_products,
        _datasets,
        _projects,
        connector,
        _audit,
        _factory,
    ) = parts

    configure_common(parts)

    mappings.get_for_owner.return_value = ChannelMapping(
        canonical_product_id="sku-1",
        channel=ChannelType.SHOPIFY,
        external_product_id="shopify-product-1",
        last_synced_hash="old-hash",
        active=True,
    )

    connector.sync_product.return_value = ConnectorResult(
        success=True,
        external_product_id="shopify-product-1",
    )

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.SUCCEEDED
    request = connector.sync_product.call_args.args[0]
    assert request.operation == "update"
    assert request.mapping.external_product_id == "shopify-product-1"


def test_connector_failure_marks_attempt_failed_and_job_failed():
    parts = make_service()
    (
        service,
        channels,
        mappings,
        sync_jobs,
        sync_attempts,
        _canonical_products,
        _datasets,
        _projects,
        connector,
        audit,
        _factory,
    ) = parts

    configure_common(parts)

    connector.sync_product.side_effect = RuntimeError(
        "remote channel unavailable"
    )

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.FAILED
    assert "remote channel unavailable" in (result.error or "")

    attempt = sync_attempts.create.call_args.kwargs["attempt"]
    assert attempt.status is SyncAttemptStatus.FAILED
    assert attempt.error == "remote channel unavailable"

    mappings.upsert.assert_not_called()

    assert audit.record.call_count == 2
    assert audit.record.call_args_list[-1].kwargs["action"] == (
        "channel.sync.failed"
    )


def test_multiple_products_use_distinct_idempotency_keys():
    parts = make_service()
    (
        service,
        _channels,
        _mappings,
        _sync_jobs,
        sync_attempts,
        canonical_products,
        _datasets,
        _projects,
        connector,
        _audit,
        _factory,
    ) = parts

    configure_common(parts)

    canonical_products.project_dataset.return_value = [
        make_product("sku-1"),
        make_product("sku-2"),
    ]

    connector.sync_product.side_effect = [
        ConnectorResult(
            success=True,
            external_product_id="external-1",
        ),
        ConnectorResult(
            success=True,
            external_product_id="external-2",
        ),
    ]

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.SUCCEEDED
    assert connector.sync_product.call_count == 2

    requests = [
        item.args[0]
        for item in connector.sync_product.call_args_list
    ]

    assert [item.idempotency_key for item in requests] == [
        "idem-1:sku-1",
        "idem-1:sku-2",
    ]

    assert sync_attempts.create.call_count == 2


def test_empty_product_set_succeeds_without_connector_calls():
    parts = make_service()
    (
        service,
        _channels,
        mappings,
        _sync_jobs,
        sync_attempts,
        canonical_products,
        _datasets,
        _projects,
        connector,
        audit,
        _factory,
    ) = parts

    configure_common(parts)
    canonical_products.project_dataset.return_value = []

    result = service.sync(
        current_user=CurrentUser(user_id="user-1"),
        channel_id="channel-1",
        dataset_id="dataset-1",
        idempotency_key="idem-1",
    )

    assert result.status is SyncJobStatus.SUCCEEDED
    connector.sync_product.assert_not_called()
    sync_attempts.create.assert_not_called()
    mappings.upsert.assert_not_called()

    started = audit.record.call_args_list[0].kwargs
    assert started["metadata"]["product_count"] == 0


