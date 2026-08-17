"""Application orchestration for the multi-agent validation workflow."""

from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

import pandas as pd
import json

from services.execution_plan_serializer import ExecutionPlanSerializer
from services.requirement_serializer import RequirementSerializer
from services.cache import TTLCache
from services.capability_execution_service import CapabilityExecutionService

from agents.requirement import RequirementAgent
from agents.reporter import ReporterAgent
from database.models import ExecutionRecord
from domain.models import ExecutionSummary

class QualityService:
    """Application service coordinating validation execution and persistence."""

    def __init__(
        self,
        *,
        requirements: RequirementAgent,
        capability_execution: CapabilityExecutionService,
        executions,
        cache: TTLCache,
        reporter: ReporterAgent,
        enable_llm: bool = False,
        llm=None,
    ) -> None:
        self._requirements = requirements
        self._capability_execution = capability_execution
        self._executions = executions
        self._cache = cache
        self._reporter = reporter
        self._enable_llm = enable_llm
        self._llm = llm

    def validate(
        self,
        frame: pd.DataFrame,
        source_bytes: bytes,
        requested_category: str | None = None,
    ) -> ExecutionSummary:
        execution_id = str(uuid4())
        source_hash = sha256(source_bytes).hexdigest()

        self._executions.create(
            ExecutionRecord(
                id=execution_id,
                category=requested_category or "unknown",
                source_hash=source_hash,
                rule_version="unknown",
                health_score=0.0,
                status="RUNNING",
            )
        )

        try:
            requirement = self._requirements.interpret(
                requested_category=requested_category,
                requested_capabilities=("data.qa",),
            )

            execution_result = self._capability_execution.execute(
                requirement=requirement,
                inputs={
                    "frame": frame,
                    "requested_category": requested_category,
                },
                execution_id=execution_id,
            )

            outputs = execution_result.outputs
            plan = execution_result.plan
            trace = execution_result.trace

            self._executions.save_execution_context(
                execution_id=execution_id,
                requirement_json=json.dumps(
                    RequirementSerializer.to_dict(requirement),
                    default=str,
                ),
                plan_json=json.dumps(
                    ExecutionPlanSerializer.to_dict(plan),
                    default=str,
                ),
                planner_version=None,
            )

            result = outputs["validation_result"]

            self._executions.save_trace(
                execution_id,
                trace,
            )

            self._executions.update_status(
                execution_id,
                "COMPLETED",
            )

        except Exception:
            self._executions.update_status(
                execution_id,
                "FAILED",
            )
            raise

        cache_key = sha256(
            source_bytes
            + result.category.encode()
            + result.rule_version.encode()
        ).hexdigest()

        cached = self._cache.get(cache_key)

        if cached is not None:
            return ExecutionSummary(
                cached.execution_id,
                cached.category,
                cached.health_score,
                cached.report_paths,
                True,
            )

        category = result.category
        version = result.rule_version
        issues = result.issues

        if self._enable_llm and self._llm is not None:
            result.metadata["llm"] = {
                "error_explanation": self._llm.explain_errors(issues),
                "suggested_fixes": self._llm.suggest_fixes(issues),
                "summary": self._llm.summarize_report(issues),
            }

        paths = self._reporter.generate(
            execution_id,
            result,
        )

        self._executions.save_result(
            execution_id=execution_id,
            category=category,
            source_hash=source_hash,
            rule_version=version,
            health_score=result.health_score,
            issues=issues,
            reports=paths,
        )

        summary = ExecutionSummary(
            execution_id,
            category,
            result.health_score,
            paths,
        )

        self._cache.set(
            cache_key,
            summary,
        )

        return summary