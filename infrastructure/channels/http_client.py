"""Bounded outbound HTTP transport for external channel connectors."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class HttpResponse:
    """Minimal transport response exposed to channel infrastructure."""

    status_code: int
    headers: Mapping[str, str]
    body: Any


class HttpClientError(RuntimeError):
    """Raised when an outbound HTTP request cannot be completed."""


class HttpClient:
    """Small synchronous HTTP transport with bounded transient retries."""

    _RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.25,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be >= 0")

        self._client = client or httpx.Client(timeout=timeout)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        json: Any = None,
    ) -> HttpResponse:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    headers=dict(headers or {}),
                    json=json,
                )
            except httpx.TransportError as exc:
                last_error = exc

                if attempt >= self._max_retries:
                    raise HttpClientError(
                        "outbound channel request failed"
                    ) from exc

                self._sleep(attempt)
                continue

            if (
                response.status_code in self._RETRYABLE_STATUS_CODES
                and attempt < self._max_retries
            ):
                self._sleep_for_response(response, attempt)
                continue

            try:
                body = response.json()
            except ValueError:
                body = response.text

            return HttpResponse(
                status_code=response.status_code,
                headers=response.headers,
                body=body,
            )

        raise HttpClientError("outbound channel request failed") from last_error

    def close(self) -> None:
        self._client.close()

    def _sleep_for_response(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> None:
        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                delay = max(0.0, float(retry_after))
            except ValueError:
                delay = self._backoff_seconds * (2**attempt)
        else:
            delay = self._backoff_seconds * (2**attempt)

        if delay > 0:
            time.sleep(delay)

    def _sleep(self, attempt: int) -> None:
        delay = self._backoff_seconds * (2**attempt)

        if delay > 0:
            time.sleep(delay)


__all__ = [
    "HttpClient",
    "HttpClientError",
    "HttpResponse",
]
