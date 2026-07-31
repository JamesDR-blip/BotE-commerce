"""Application orchestration for the multi-agent validation workflow."""
from __future__ import annotations
from hashlib import sha256
from uuid import uuid4
import pandas as pd
from database.models import ExecutionRecord
from domain.models import ExecutionSummary
from services.container import Container


class QualityService:
    def __init__(self, container: Container) -> None: self._container = container
    def validate(self, frame: pd.DataFrame, source_bytes: bytes, requested_category: str | None = None) -> ExecutionSummary:
        result = self._container.workflow.run(frame, requested_category)
        cache_key = sha256(source_bytes + result.category.encode() + result.rule_version.encode()).hexdigest()
        cached = self._container.cache.get(cache_key)
        if cached is not None: return ExecutionSummary(cached.execution_id, cached.category, cached.health_score, cached.report_paths, True)
        category, version, issues = result.category, result.rule_version, result.issues
        if self._container.settings.enable_llm:
            result.metadata["llm"] = {
                "error_explanation": self._container.llm.explain_errors(issues),
                "suggested_fixes": self._container.llm.suggest_fixes(issues),
                "summary": self._container.llm.summarize_report(issues),
            }
        execution_id = str(uuid4()); paths = self._container.reporter.generate(execution_id, result)
        self._container.executions.save(ExecutionRecord(id=execution_id, category=category, source_hash=sha256(source_bytes).hexdigest(), rule_version=version, health_score=result.health_score), issues, paths)
        summary = ExecutionSummary(execution_id, category, result.health_score, paths)
        self._container.cache.set(cache_key, summary)
        return summary
