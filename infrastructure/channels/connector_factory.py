"""Infrastructure factory for channel connectors."""

from __future__ import annotations

import json
from typing import Any

from domain.channel_sync import ChannelType, Connector
from infrastructure.channels.amazon_sp_api_connector import AmazonSPAPIConnector
from infrastructure.channels.http_client import HttpClient
from infrastructure.channels.shopify_connector import ShopifyConnector


class ChannelConnectorFactory:
    """Build a connector from encrypted-at-rest credentials after decryption."""

    def __init__(self, *, http_client: HttpClient) -> None:
        self._http_client = http_client

    def create(
        self,
        *,
        channel: ChannelType,
        credentials: str,
    ) -> Connector:
        try:
            config = json.loads(credentials)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid channel credential configuration") from exc

        if not isinstance(config, dict):
            raise ValueError("invalid channel credential configuration")

        if channel is ChannelType.SHOPIFY:
            return ShopifyConnector(
                http_client=self._http_client,
                base_url=self._required_string(config, "base_url"),
                access_token=self._required_string(config, "access_token"),
            )

        if channel is ChannelType.AMAZON_SP_API:
            return AmazonSPAPIConnector(
                http_client=self._http_client,
                base_url=self._required_string(config, "base_url"),
                access_token=self._required_string(config, "access_token"),
                marketplace_id=self._required_string(
                    config,
                    "marketplace_id",
                ),
            )

        raise ValueError(
            f"connector is not implemented for channel: {channel.value}"
        )

    @staticmethod
    def _required_string(
        config: dict[str, Any],
        key: str,
    ) -> str:
        value = config.get(key)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"channel credential field is required: {key}"
            )

        return value
