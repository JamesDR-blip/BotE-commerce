"""Shopify connector implementation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from domain.channel_sync import (
    ChannelType,
    Connector,
    ConnectorRequest,
    ConnectorResult,
)
from infrastructure.channels.http_client import HttpClient


class ShopifyConnector:
    """Synchronize canonical products through a Shopify Admin API boundary."""

    def __init__(
        self,
        *,
        http_client: HttpClient,
        base_url: str,
        access_token: str,
    ) -> None:
        if not base_url.strip():
            raise ValueError("Shopify base URL is required")
        if not access_token.strip():
            raise ValueError("Shopify access token is required")

        self._http = http_client
        self._base_url = base_url.rstrip("/")
        self._access_token = access_token

    @property
    def channel(self) -> ChannelType:
        return ChannelType.SHOPIFY

    def sync_product(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResult:
        if request.operation == "noop":
            return ConnectorResult(
                success=True,
                external_product_id=(
                    request.mapping.external_product_id
                    if request.mapping
                    else request.product.product_id
                ),
                remote_hash=(
                    request.mapping.last_synced_hash
                    if request.mapping
                    else ""
                ),
                message="no changes required",
            )

        payload = self._payload(request)

        if request.operation == "create":
            method = "POST"
            url = f"{self._base_url}/admin/api/2025-10/products.json"
        else:
            external_id = self._require_external_id(request)
            method = "PUT"
            url = (
                f"{self._base_url}/admin/api/2025-10/products/"
                f"{external_id}.json"
            )

        response = self._http.request(
            method=method,
            url=url,
            headers={
                "X-Shopify-Access-Token": self._access_token,
                "Content-Type": "application/json",
                "Idempotency-Key": request.idempotency_key,
            },
            json=payload,
        )

        if response.status_code >= 400:
            return ConnectorResult(
                success=False,
                message=self._safe_error_message(response.body),
                retryable=response.status_code
                in {429, 502, 503, 504},
            )

        external_id = self._extract_product_id(response.body)

        if not external_id:
            return ConnectorResult(
                success=False,
                message="Shopify response did not contain a product id",
            )

        return ConnectorResult(
            success=True,
            external_product_id=external_id,
            remote_hash=self._hash_payload(payload),
            message="Shopify product synchronized",
        )

    @staticmethod
    def _payload(request: ConnectorRequest) -> dict[str, Any]:
        product = request.product

        return {
            "product": {
                "title": product.title,
                "vendor": product.brand,
                "variants": [
                    {
                        "sku": product.sku,
                        "price": product.price,
                    }
                ],
                "metafields": [
                    {
                        "namespace": "canonical",
                        "key": "product_id",
                        "value": product.product_id,
                        "type": "single_line_text_field",
                    }
                ],
            }
        }

    @staticmethod
    def _extract_product_id(body: Any) -> str:
        if not isinstance(body, dict):
            return ""

        product = body.get("product")

        if not isinstance(product, dict):
            return ""

        value = product.get("id")

        return str(value) if value is not None else ""

    @staticmethod
    def _safe_error_message(body: Any) -> str:
        if isinstance(body, dict):
            errors = body.get("errors")

            if isinstance(errors, str):
                return errors

            if errors:
                return "Shopify request rejected"

        return "Shopify request failed"

    @staticmethod
    def _require_external_id(request: ConnectorRequest) -> str:
        if request.mapping is None:
            raise ValueError("update operation requires external product id")

        if not request.mapping.external_product_id.strip():
            raise ValueError("update operation requires external product id")

        return request.mapping.external_product_id

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


Connector = ShopifyConnector

