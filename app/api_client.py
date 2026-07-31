"""Typed HTTP boundary used by the Streamlit dashboard."""
from __future__ import annotations

from dataclasses import dataclass

import httpx


class DashboardApiError(RuntimeError):
    """Raised when the FastAPI backend cannot fulfil a dashboard request."""


@dataclass(frozen=True)
class ValidationSummary:
    execution_id: str
    category: str
    health_score: float
    reports: dict[str, str]
    cached: bool


class DashboardApiClient:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=base_url.rstrip("/"), timeout=30.0)

    def categories(self) -> list[str]:
        return self._request("GET", "/categories").json()["categories"]

    def validate(self, filename: str, content: bytes, content_type: str | None, category: str | None) -> ValidationSummary:
        data = {"category": category} if category else None
        response = self._request(
            "POST", "/validate", data=data, files={"file": (filename, content, content_type or "application/octet-stream")}
        ).json()
        return ValidationSummary(**response)

    def history(self) -> list[dict[str, object]]:
        return self._request("GET", "/history").json()["items"]

    def download_report(self, path: str) -> bytes:
        return self._request("GET", path).content

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            detail = ""
            if isinstance(exc, httpx.HTTPStatusError):
                try:
                    detail = exc.response.json().get("detail", "")
                except ValueError:
                    detail = exc.response.text
            raise DashboardApiError(detail or "Could not communicate with the FastAPI backend") from exc
