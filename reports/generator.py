"""Excel, HTML, PDF and JSON report generators."""
from __future__ import annotations
import html, json
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from domain.models import ValidationResult


class ReportAgent:
    def __init__(self, directory: Path) -> None: self._directory = directory
    def generate(self, execution_id: str, result: ValidationResult) -> dict[str, str]:
        base = self._directory / execution_id; base.mkdir(parents=True, exist_ok=True)
        excel, html_path, pdf, json_path = base / "report.xlsx", base / "report.html", base / "report.pdf", base / "report.json"
        with pd.ExcelWriter(excel) as writer:
            result.clean.to_excel(writer, sheet_name="clean", index=False)
            result.quarantine.to_excel(writer, sheet_name="quarantine", index=False)
        payload = {"execution_id": execution_id, "category": result.category, "health_score": result.health_score, "rule_version": result.rule_version, "issues": [x.__dict__ for x in result.issues], "anomaly_count": result.anomaly_count, "metadata": result.metadata}
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        html_path.write_text(f"<html><body><h1>Data Quality Report</h1><p>Category: {html.escape(result.category)}</p><h2>{result.health_score:.2f}%</h2><p>Issues: {len(result.issues)}</p></body></html>", encoding="utf-8")
        canvas = Canvas(str(pdf), pagesize=A4); canvas.drawString(72, 780, "Data Quality Report"); canvas.drawString(72, 755, f"Category: {result.category}"); canvas.drawString(72, 730, f"Health score: {result.health_score:.2f}%"); canvas.save()
        return {"excel": str(excel), "html": str(html_path), "pdf": str(pdf), "json": str(json_path)}
