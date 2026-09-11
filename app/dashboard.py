"""Streamlit dashboard, run with: ``streamlit run app/dashboard.py``."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:  # ``streamlit run app/dashboard.py`` executes from the app directory.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

try:  # Supports both ``streamlit run dashboard.py`` and ``streamlit run app/dashboard.py``.
    from app.api_client import (
    DashboardApiClient,
    DashboardApiError,
    DatasetHealth,
    Diagnostics,
    HealthMetrics,
    ValidationSummary,
)
except ModuleNotFoundError:  # pragma: no cover - depends on Streamlit's script path setup.
    from api_client import (
    DashboardApiClient,
    DashboardApiError,
    DatasetHealth,
    Diagnostics,
    HealthMetrics,
    ValidationSummary,
)
from configs.settings import Settings


@st.cache_resource
def _api_client(base_url: str) -> DashboardApiClient:
    return DashboardApiClient(base_url)


def _render_result(client: DashboardApiClient, result: ValidationSummary) -> None:
    st.subheader("Validation result")
    left, middle, right = st.columns(3)
    left.metric("Health score", f"{result.health_score:.2f}%")
    middle.metric("Category", result.category)
    right.metric("Execution", result.execution_id[:8])
    if result.cached:
        st.info("This result was served from the backend cache.")
    st.subheader("Reports")
    for report_format, path in result.reports.items():
        try:
            content = client.download_report(path)
            st.download_button(
                f"Download {report_format.upper()}",
                data=content,
                file_name=f"data-quality-report.{report_format}",
                key=f"report-{result.execution_id}-{report_format}",
            )
        except DashboardApiError as exc:
            st.warning(f"{report_format.upper()} report is unavailable: {exc}")


def _render_data_health(client: DashboardApiClient) -> None:
    workspace_id = st.text_input(
        "Workspace ID",
        value=st.session_state.get("health_workspace_id", ""),
        key="health_workspace_id",
        help="Required because the existing API scopes projects by workspace.",
    )

    if not workspace_id:
        st.info("Enter a workspace ID to open the Data Health Command Center.")
        return

    try:
        projects = client.projects(workspace_id)
    except DashboardApiError as exc:
        st.error(f"Could not load projects: {exc}")
        return

    if not projects:
        st.info("No projects are available in this workspace.")
        return

    project_options = {project.name: project.id for project in projects}
    project_name = st.selectbox(
        "Health project",
        list(project_options),
        key="health_project_name",
    )
    project_id = project_options[project_name]

    try:
        health = client.health_metrics(project_id)
    except DashboardApiError as exc:
        st.error(f"Could not load health metrics: {exc}")
        return

    st.subheader("Data Health Command Center")

    if not health.items:
        st.info("No datasets are available for this project.")
        return

    overall = sum(item.aggregate for item in health.items) / len(health.items)
    st.metric("Project health", f"{overall:.2f}%")

    rows = []
    severity_counts: dict[str, int] = {}

    for dataset in health.items:
        row = {
            "Dataset": dataset.dataset_name,
            "Health": dataset.aggregate,
        }
        for metric in dataset.metrics:
            row[metric.dimension.title()] = (
                metric.score if metric.assessed else None
            )
        rows.append(row)

    frame = pd.DataFrame(rows)
    st.dataframe(frame, use_container_width=True, hide_index=True)

    st.subheader("Health dimensions")
    if not frame.empty:
        dimensions = [
            column
            for column in frame.columns
            if column not in {"Dataset", "Health"}
        ]
        if dimensions:
            st.bar_chart(
                frame.set_index("Dataset")[dimensions],
                use_container_width=True,
            )

    st.subheader("Diagnostics")

    for dataset in health.items:
        try:
            diagnostics = client.diagnostics(dataset.dataset_id)
        except DashboardApiError as exc:
            st.warning(
                f"Could not load diagnostics for {dataset.dataset_name}: {exc}"
            )
            continue

        for diagnostic in diagnostics.diagnostics:
            severity = diagnostic.severity.lower()
            severity_counts[severity] = (
                severity_counts.get(severity, 0) + diagnostic.count
            )

    if severity_counts:
        severity_frame = pd.DataFrame(
            [{"Severity": key, "Count": value}
             for key, value in sorted(severity_counts.items())]
        )
        st.bar_chart(
            severity_frame.set_index("Severity"),
            use_container_width=True,
        )
    else:
        st.info("No diagnostics were detected.")

    selected_dataset = st.selectbox(
        "Dataset diagnostics",
        health.items,
        format_func=lambda item: item.dataset_name,
        key="health_dataset",
    )

    try:
        diagnostics = client.diagnostics(selected_dataset.dataset_id)
    except DashboardApiError as exc:
        st.error(f"Could not load diagnostics: {exc}")
        return

    if diagnostics.diagnostics:
        diagnostic_frame = pd.DataFrame(
            [
                {
                    "Code": item.code,
                    "Field": item.field,
                    "Severity": item.severity,
                    "Count": item.count,
                    "Message": item.message,
                }
                for item in diagnostics.diagnostics
            ]
        )
        st.dataframe(
            diagnostic_frame,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No diagnostics detected for this dataset.")

    st.subheader("Remediation preview")

    if not diagnostics.remediation_proposals:
        st.info("No remediation proposals are available.")
        return

    proposal_frame = pd.DataFrame(
        [
            {
                "Status": proposal.status,
                "Severity": proposal.severity,
                "Action": proposal.action,
                "Rationale": proposal.rationale,
            }
            for proposal in diagnostics.remediation_proposals
        ]
    )
    st.dataframe(
        proposal_frame,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Remediation proposals are read-only previews. "
        "No remediation action is executed from this dashboard."
    )


def _render_history(client: DashboardApiClient) -> None:
    st.subheader("Execution history")
    try:
        history = client.history()
    except DashboardApiError as exc:
        st.error(f"Could not load history: {exc}")
        return
    if not history:
        st.info("No executions have been recorded yet.")
        return
    frame = pd.DataFrame(history)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.subheader("Health score trend")
    chart = frame.loc[:, ["created_at", "health_score"]].copy()
    chart["created_at"] = pd.to_datetime(chart["created_at"])
    st.line_chart(chart.set_index("created_at"), y="health_score")


def main() -> None:
    settings = Settings()
    st.set_page_config(page_title="AI Studio E-commerce Platform", layout="wide")
    st.title("AI Studio E-commerce Platform")
    st.caption(f"Connected to FastAPI: {settings.api_base_url}")
    client = _api_client(settings.api_base_url)
    try:
        categories = client.categories()
    except DashboardApiError as exc:
        st.error(f"FastAPI backend is unavailable: {exc}")
        return
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    category = st.selectbox("Category", ["Auto detect", *categories])
    if uploaded is not None and st.button("Validate", type="primary"):
        with st.spinner("Validating data through FastAPI…"):
            try:
                result = client.validate(
                    uploaded.name, uploaded.getvalue(), uploaded.type,
                    None if category == "Auto detect" else category,
                )
                st.session_state["validation_result"] = result
            except DashboardApiError as exc:
                st.error(f"Validation failed: {exc}")
    result = st.session_state.get("validation_result")
    if result:
        _render_result(client, result)

    _render_data_health(client)
    _render_history(client)


if __name__ == "__main__":
    main()
