"""Streamlit dashboard, run with: streamlit run dashboard.py"""
from io import BytesIO
import pandas as pd
import streamlit as st
from configs.settings import Settings
from services.container import Container
from services.quality_service import QualityService

st.set_page_config(page_title="AI Data Quality Platform", layout="wide")
st.title("AI Data Quality Platform")
container = Container(Settings()); service = QualityService(container)
uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
category = st.selectbox("Category", ["Auto detect", *container.registry.categories()])
if uploaded and st.button("Validate"):
    data = uploaded.getvalue(); frame = pd.read_csv(BytesIO(data)) if uploaded.name.lower().endswith(".csv") else pd.read_excel(BytesIO(data))
    result = service.validate(frame, data, None if category == "Auto detect" else category)
    st.metric("Health score", f"{result.health_score:.2f}%"); st.json(result.report_paths)
st.subheader("Execution history")
st.dataframe(pd.DataFrame([{"id": x.id, "category": x.category, "score": x.health_score, "created": x.created_at} for x in container.executions.history()]))
