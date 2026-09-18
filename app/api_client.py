"""Typed HTTP boundary used by the Streamlit dashboard."""
from __future__ import annotations

from dataclasses import dataclass
import json

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


@dataclass(frozen=True)
class ProjectSummary:
    id: str
    workspace_id: str
    name: str
    description: str | None = None


@dataclass(frozen=True)
class HealthMetric:
    dimension: str
    score: float
    assessed: bool


@dataclass(frozen=True)
class DatasetHealth:
    dataset_id: str
    dataset_name: str
    aggregate: float
    metrics: list[HealthMetric]


@dataclass(frozen=True)
class HealthMetrics:
    project_id: str
    items: list[DatasetHealth]


@dataclass(frozen=True)
class Diagnostic:
    code: str
    field: str
    message: str
    severity: str
    count: int


@dataclass(frozen=True)
class RemediationProposal:
    id: str
    diagnostic_code: str
    action: str
    rationale: str
    severity: str
    status: str


@dataclass(frozen=True)
class Diagnostics:
    dataset_id: str
    diagnostics: list[Diagnostic]
    remediation_proposals: list[RemediationProposal]


@dataclass(frozen=True)
class CopilotSession:
    session_id: str


@dataclass(frozen=True)
class CopilotEvent:
    type: str
    content: str | None = None
    action: str | None = None
    arguments: dict[str, object] | None = None
    approval: dict[str, object] | None = None


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

    def projects(self, workspace_id: str) -> list[ProjectSummary]:
        payload = self._request(
            "GET",
            f"/workspaces/{workspace_id}/projects",
        ).json()
        return [
            ProjectSummary(
                id=item["id"],
                workspace_id=item["workspace_id"],
                name=item["name"],
                description=item.get("description"),
            )
            for item in payload
        ]

    def health_metrics(self, project_id: str) -> HealthMetrics:
        payload = self._request(
            "GET",
            "/health-metrics",
            params={"project_id": project_id},
        ).json()

        return HealthMetrics(
            project_id=payload["project_id"],
            items=[
                DatasetHealth(
                    dataset_id=item["dataset_id"],
                    dataset_name=item["dataset_name"],
                    aggregate=item["aggregate"],
                    metrics=[
                        HealthMetric(
                            dimension=metric["dimension"],
                            score=metric["score"],
                            assessed=metric["assessed"],
                        )
                        for metric in item["metrics"]
                    ],
                )
                for item in payload["items"]
            ],
        )

    def diagnostics(self, dataset_id: str) -> Diagnostics:
        payload = self._request(
            "GET",
            f"/diagnostics/{dataset_id}",
        ).json()

        return Diagnostics(
            dataset_id=payload["dataset_id"],
            diagnostics=[
                Diagnostic(
                    code=item["code"],
                    field=item["field"],
                    message=item["message"],
                    severity=item["severity"],
                    count=item["count"],
                )
                for item in payload["diagnostics"]
            ],
            remediation_proposals=[
                RemediationProposal(
                    id=item["id"],
                    diagnostic_code=item["diagnostic_code"],
                    action=item["action"],
                    rationale=item["rationale"],
                    severity=item["severity"],
                    status=item["status"],
                )
                for item in payload["remediation_proposals"]
            ],
        )

    def download_report(self, path: str) -> bytes:
        return self._request("GET", path).content

    def create_copilot_session(self) -> CopilotSession:
        payload = self._request("POST", "/copilot/sessions").json()
        return CopilotSession(session_id=payload["session_id"])

    def stream_copilot(
        self,
        message: str,
        *,
        session_id: str | None = None,
        authorization: str | None = None,
    ):
        headers = {"Authorization": authorization} if authorization else None

        try:
            with self._client.stream(
                "POST",
                "/copilot/chat",
                json={"message": message, "session_id": session_id},
                headers=headers,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        payload = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    yield CopilotEvent(
                        type=payload["type"],
                        content=payload.get("content"),
                        action=payload.get("action"),
                        arguments=payload.get("arguments"),
                        approval=payload.get("approval"),
                    )
        except httpx.HTTPError as exc:
            detail = ""
            if isinstance(exc, httpx.HTTPStatusError):
                try:
                    detail = exc.response.json().get("detail", "")
                except ValueError:
                    detail = exc.response.text
            raise DashboardApiError(detail or "Could not communicate with the FastAPI backend") from exc

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
