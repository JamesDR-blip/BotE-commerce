"""Amazon SP-API connector implementation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from domain.channel_sync import (
    ChannelType,
    ConnectorRequest,
    ConnectorResult,
)
from infrastructure.channels.http_client import HttpClient


class AmazonSPAPIConnector:
    """Synchronize canonical products through an Amazon SP-API boundary."""

    def __init__(
        self,
        *,
        http_client: HttpClient,
        base_url: str,
        access_token: str,
        marketplace_id: str,
    ) -> None:
        if not base_url.strip():
            raise ValueError("Amazon SP-API base URL is required")
        if not access_token.strip():
            raise ValueError("Amazon SP-API access token is required")
        if not marketplace_id.strip():
            raise ValueError("Amazon marketplace id is required")

        self._http = http_client
        self._base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._marketplace_id = marketplace_id

    @property
    def channel(self) -> ChannelType:
        return ChannelType.AMAZON_SP_API

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

        external_id = (
            request.mapping.external_product_id
            if request.mapping
            else ""
        )

        if request.operation == "update" and not external_id:
            raise ValueError(
                "update operation requires external product id"
            )

        url = (
            f"{self._base_url}/listings/2021-08-01/items/"
            f"SYNC/{external_id or request.product.sku}"
        )

        response = self._http.request(
            method="PUT",
            url=url,
            headers={
                "x-amz-access-token": self._access_token,
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

        remote_id = external_id or request.product.sku

        if not remote_id:
            return ConnectorResult(
                success=False,
                message="Amazon response could not establish product identity",
            )

        return ConnectorResult(
            success=True,
            external_product_id=remote_id,
            remote_hash=self._hash_payload(payload),
            message="Amazon product synchronized",
        )

    def _payload(self, request: ConnectorRequest) -> dict[str, Any]:
        product = request.product

        return {
            "productType": "PRODUCT",
            "requirements": "LISTING",
            "attributes": {
                "item_name": [
                    {
                        "value": product.title,
                        "marketplace_id": self._marketplace_id,
                    }
                ],
                "brand": [
                    {
                        "value": product.brand,
                        "marketplace_id": self._marketplace_id,
                    }
                ],
                "sku": [
                    {
                        "value": product.sku,
                        "marketplace_id": self._marketplace_id,
                    }
                ],
                "price": [
                    {
                        "value": product.price,
                        "marketplace_id": self._marketplace_id,
                    }
                ],
            },
        }

    @staticmethod
    def _safe_error_message(body: Any) -> str:
        if isinstance(body, dict):
            errors = body.get("errors")

            if isinstance(errors, list) and errors:
                return "Amazon SP-API request rejected"

        return "Amazon SP-API request failed"

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


Connector = AmazonSPAPIConnector
