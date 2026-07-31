"""Streamlit dashboard, run with: ``streamlit run app/dashboard.py``."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:  # ``streamlit run app/dashboard.py`` executes from the app directory.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

try:  # Supports both ``streamlit run dashboard.py`` and ``streamlit run app/dashboard.py``.
    from app.api_client import DashboardApiClient, DashboardApiError, ValidationSummary
except ModuleNotFoundError:  # pragma: no cover - depends on Streamlit's script path setup.
    from api_client import DashboardApiClient, DashboardApiError, ValidationSummary
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
    st.set_page_config(page_title="AI Data Quality Platform", layout="wide")
    st.title("AI Data Quality Platform")
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
    _render_history(client)


if __name__ == "__main__":
    main()
