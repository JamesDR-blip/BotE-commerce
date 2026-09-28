"""Infrastructure factory for channel connectors."""

from __future__ import annotations

import ipaddress
import json
from urllib.parse import urlsplit
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
                base_url=self._validated_base_url(config),
                access_token=self._required_string(config, "access_token"),
            )

        if channel is ChannelType.AMAZON_SP_API:
            return AmazonSPAPIConnector(
                http_client=self._http_client,
                base_url=self._validated_base_url(config),
                access_token=self._required_string(config, "access_token"),
                marketplace_id=self._required_string(
                    config,
                    "marketplace_id",
                ),
            )

        raise ValueError(
            f"connector is not implemented for channel: {channel.value}"
        )

    @classmethod
    def _validated_base_url(
        cls,
        config: dict[str, Any],
    ) -> str:
        value = cls._required_string(config, "base_url").strip()
        parsed = urlsplit(value)

        if parsed.scheme.lower() != "https":
            raise ValueError("channel base_url must use https")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError(
                "channel base_url must not contain credentials"
            )

        hostname = parsed.hostname
        if not hostname:
            raise ValueError(
                "channel base_url must contain a hostname"
            )

        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError(
                "channel base_url must identify an origin only"
            )

        normalized_host = hostname.rstrip(".").lower()

        if (
            normalized_host in {"localhost", "localhost.localdomain"}
            or normalized_host.endswith(".localhost")
            or normalized_host.endswith(".local")
        ):
            raise ValueError(
                "channel base_url must not target a local hostname"
            )

        try:
            address = ipaddress.ip_address(normalized_host)
        except ValueError:
            address = None

        if address is not None and (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise ValueError(
                "channel base_url must not target a reserved or private address"
            )

        return value

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
