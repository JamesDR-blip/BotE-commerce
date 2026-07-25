"""Numerical anomaly detection isolated from business validators."""
from __future__ import annotations
import pandas as pd

def detect_anomalies(frame: pd.DataFrame) -> set[int]:
    numeric = frame.select_dtypes(include="number").dropna(axis=1)
    if len(numeric) < 10 or numeric.shape[1] == 0: return set()
    from sklearn.ensemble import IsolationForest
    labels = IsolationForest(contamination="auto", random_state=42).fit_predict(numeric.fillna(numeric.median()))
    return set(numeric.index[labels == -1])
