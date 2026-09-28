import json
import httpx
import pytest

from domain.channel_sync import (
    CanonicalProduct,
    ChannelMapping,
    ChannelType,
    ConnectorRequest,
)
from infrastructure.channels.amazon_sp_api_connector import (
    AmazonSPAPIConnector,
)
from infrastructure.channels.connector_factory import ChannelConnectorFactory
from infrastructure.channels.http_client import (
    HttpClient,
    HttpClientError,
)
from infrastructure.channels.shopify_connector import ShopifyConnector


def _product() -> CanonicalProduct:
    return CanonicalProduct(
        product_id="SKU-1",
        title="Portable Fan",
        sku="SKU-1",
        brand="Acme",
        price="100.00",
    )


def _request(
    *,
    operation: str,
    mapping: ChannelMapping | None = None,
) -> ConnectorRequest:
    return ConnectorRequest(
        product=_product(),
        mapping=mapping,
        operation=operation,
        idempotency_key="sync-key-1",
    )


def _factory() -> ChannelConnectorFactory:
    return ChannelConnectorFactory(
        http_client=HttpClient(max_retries=0),
    )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://example.test",
        "ftp://example.test",
        "example.test",
        "https://user:pass@example.test",
        "https://localhost",
        "https://service.local",
        "https://127.0.0.1",
        "https://10.0.0.10",
        "https://172.16.0.10",
        "https://192.168.1.10",
        "https://169.254.1.10",
        "https://[::1]",
        "https://[fd00::1]",
        "https://example.test/products",
        "https://example.test?redirect=internal",
    ],
)
def test_channel_connector_factory_rejects_unsafe_base_url(
    base_url: str,
) -> None:
    credentials = {
        "base_url": base_url,
        "access_token": "secret-token",
    }

    with pytest.raises(ValueError, match="channel base_url"):
        _factory().create(
            channel=ChannelType.SHOPIFY,
            credentials=json.dumps(credentials),
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "https://shopify.test",
        "https://amazon.test/",
    ],
)
def test_channel_connector_factory_accepts_https_origin(
    base_url: str,
) -> None:
    credentials = {
        "base_url": base_url,
        "access_token": "secret-token",
    }

    connector = _factory().create(
        channel=ChannelType.SHOPIFY,
        credentials=json.dumps(credentials),
    )

    assert isinstance(connector, ShopifyConnector)


def test_http_client_retries_transient_status(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"ok": True},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        http = HttpClient(
            client=client,
            max_retries=1,
            backoff_seconds=0,
        )

        response = http.request(
            method="GET",
            url="https://example.test",
        )

    assert response.status_code == 200
    assert len(calls) == 2


def test_http_client_does_not_retry_non_transient_4xx() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            400,
            request=request,
            json={"errors": "invalid"},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        http = HttpClient(
            client=client,
            max_retries=2,
            backoff_seconds=0,
        )

        response = http.request(
            method="POST",
            url="https://example.test",
        )

    assert response.status_code == 400
    assert len(calls) == 1


def test_http_client_fails_after_bounded_transport_retries() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        raise httpx.ConnectError("network failure", request=request)

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        http = HttpClient(
            client=client,
            max_retries=2,
            backoff_seconds=0,
        )

        with pytest.raises(HttpClientError):
            http.request(
                method="GET",
                url="https://example.test",
            )

    assert len(calls) == 3


def test_shopify_create_propagates_idempotency_and_returns_external_id() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["json"] = request.read().decode("utf-8")

        return httpx.Response(
            201,
            request=request,
            json={"product": {"id": 12345}},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        connector = ShopifyConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://shopify.test",
            access_token="secret-token",
        )

        result = connector.sync_product(
            _request(operation="create")
        )

    assert result.success is True
    assert result.external_product_id == "12345"
    assert captured["headers"]["idempotency-key"] == "sync-key-1"
    assert "secret-token" not in captured["json"]


def test_shopify_update_requires_external_identity() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            request=request,
            json={"product": {"id": 1}},
        )
    )

    with httpx.Client(transport=transport) as client:
        connector = ShopifyConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://shopify.test",
            access_token="secret-token",
        )

        with pytest.raises(
            ValueError,
            match="external product id",
        ):
            connector.sync_product(
                _request(operation="update")
            )


def test_shopify_429_is_reported_as_retryable() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            429,
            request=request,
            json={"errors": "rate limited"},
        )
    )

    with httpx.Client(transport=transport) as client:
        connector = ShopifyConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://shopify.test",
            access_token="secret-token",
        )

        result = connector.sync_product(
            _request(operation="create")
        )

    assert result.success is False
    assert result.retryable is True
    assert "secret-token" not in result.message


def test_amazon_create_returns_sku_identity() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        return httpx.Response(
            200,
            request=request,
            json={"status": "ACCEPTED"},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        connector = AmazonSPAPIConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://amazon.test",
            access_token="secret-token",
            marketplace_id="ATVPDKIKX0DER",
        )

        result = connector.sync_product(
            _request(operation="create")
        )

    assert result.success is True
    assert result.external_product_id == "SKU-1"
    assert captured["headers"]["idempotency-key"] == "sync-key-1"
    assert captured["headers"]["x-amz-access-token"] == "secret-token"


def test_amazon_update_requires_external_identity() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            request=request,
            json={"status": "ACCEPTED"},
        )
    )

    with httpx.Client(transport=transport) as client:
        connector = AmazonSPAPIConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://amazon.test",
            access_token="secret-token",
            marketplace_id="ATVPDKIKX0DER",
        )

        with pytest.raises(
            ValueError,
            match="external product id",
        ):
            connector.sync_product(
                _request(operation="update")
            )


def test_connectors_support_noop_without_http_call() -> None:
    def fail_handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("noop must not make an HTTP request")

    transport = httpx.MockTransport(fail_handler)

    with httpx.Client(transport=transport) as client:
        connector = ShopifyConnector(
            http_client=HttpClient(
                client=client,
                max_retries=0,
            ),
            base_url="https://shopify.test",
            access_token="secret-token",
        )

        result = connector.sync_product(
            _request(
                operation="noop",
                mapping=ChannelMapping(
                    canonical_product_id="SKU-1",
                    channel=ChannelType.SHOPIFY,
                    external_product_id="shopify-1",
                    last_synced_hash="hash-1",
                ),
            )
        )

    assert result.success is True
    assert result.external_product_id == "shopify-1"
    assert result.remote_hash == "hash-1"
