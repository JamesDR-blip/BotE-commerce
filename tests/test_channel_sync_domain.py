from domain.channel_sync import (
    CanonicalProduct,
    ChannelMapping,
    ChannelType,
    ConnectorRequest,
    ConnectorResult,
    SyncAttempt,
    SyncAttemptStatus,
    SyncJob,
    SyncJobStatus,
    SyncTransitionError,
)


def _job() -> SyncJob:
    return SyncJob(
        id="job-1",
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        channel_id="ch-1",
        idempotency_key="dataset-1:shopify:product-1:hash-1",
    )


def test_canonical_product_requires_identity_and_title() -> None:
    product = CanonicalProduct(
        product_id="product-1",
        title="Portable Mini Fan",
    )

    assert product.product_id == "product-1"
    assert product.title == "Portable Mini Fan"
    assert product.attributes == {}


def test_channel_mapping_preserves_external_identity() -> None:
    mapping = ChannelMapping(
        canonical_product_id="product-1",
        channel=ChannelType.AMAZON_SP_API,
        external_product_id="ASIN-123",
        last_synced_hash="abc123",
    )

    assert mapping.external_product_id == "ASIN-123"
    assert mapping.last_synced_hash == "abc123"


def test_sync_job_has_explicit_state_transitions() -> None:
    running = _job().transition(SyncJobStatus.RUNNING)
    succeeded = running.transition(SyncJobStatus.SUCCEEDED)

    assert running.status is SyncJobStatus.RUNNING
    assert succeeded.status is SyncJobStatus.SUCCEEDED


def test_sync_job_rejects_invalid_transition() -> None:
    succeeded = _job().transition(SyncJobStatus.RUNNING).transition(
        SyncJobStatus.SUCCEEDED
    )

    try:
        succeeded.transition(SyncJobStatus.RUNNING)
    except SyncTransitionError:
        pass
    else:
        raise AssertionError("expected SyncTransitionError")


def test_failed_sync_job_requires_error() -> None:
    running = _job().transition(SyncJobStatus.RUNNING)

    try:
        running.transition(SyncJobStatus.FAILED)
    except ValueError as exc:
        assert "error" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_connector_request_rejects_unknown_operation() -> None:
    product = CanonicalProduct(product_id="product-1", title="Fan")

    try:
        ConnectorRequest(
            product=product,
            mapping=None,
            operation="delete",
            idempotency_key="key-1",
        )
    except ValueError as exc:
        assert "unsupported connector operation" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_successful_connector_result_requires_external_id() -> None:
    try:
        ConnectorResult(success=True)
    except ValueError as exc:
        assert "external_product_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_failed_attempt_requires_error() -> None:
    try:
        SyncAttempt(
            id="attempt-1",
            sync_job_id="job-1",
            attempt_number=1,
            status=SyncAttemptStatus.FAILED,
            request_hash="hash-1",
        )
    except ValueError as exc:
        assert "error" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_valid_sync_attempt() -> None:
    attempt = SyncAttempt(
        id="attempt-1",
        sync_job_id="job-1",
        attempt_number=1,
        status=SyncAttemptStatus.SUCCEEDED,
        request_hash="hash-1",
        external_product_id="external-1",
    )

    assert attempt.attempt_number == 1
    assert attempt.external_product_id == "external-1"
