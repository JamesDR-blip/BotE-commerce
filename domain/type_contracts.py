from __future__ import annotations

import pandas as pd


TYPE_CONTRACTS = {
    "frame": pd.DataFrame,
    "category": str,
    "issues": list,
    "rule_version": str,
    "extractions": list,
    "validation_result": object,
}