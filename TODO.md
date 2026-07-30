# Prioritized TODO

This backlog is ordered by risk and dependency. Deliver one slice at a time while preserving existing endpoints until an equivalent replacement is released.

## P0 — Complete before expanding features

- [ ] Route every upload path, including Streamlit, through one ingestion service with consistent format, size, and spreadsheet-formula protections.
- [ ] Enforce request-size limits before buffering the full request; document reverse-proxy and application settings.
- [ ] Add authentication and user/tenant ownership to executions and reports; authorize history and report downloads.
- [ ] Replace direct database report paths with authorized artifact IDs and enforce report-root containment.
- [ ] Remove committed PostgreSQL credentials from deployment defaults; document secret injection and production variables.
- [ ] Add negative security tests for path-like names, oversized bodies, malformed spreadsheets, formula cells, unauthorized reports, and report-path escape.

## P1 — Make the validation core durable

- [ ] Add Alembic and an initial migration for execution, report, and validation-log tables.
- [ ] Remove schema creation from ordinary application startup; provide explicit development/bootstrap commands.
- [ ] Add typed application commands/results for ingestion, validation, execution history, and artifact retrieval.
- [ ] Add a persisted execution/job state machine: queued, running, completed, failed, cancelled; include step timing and error details.
- [ ] Move long-running validation, reports, anomaly detection, and LLM enrichment to background workers.
- [ ] Add an `ArtifactStore` abstraction: local first, S3-compatible later, with retention and cleanup.
- [ ] Replace the unbounded per-process cache with bounded shared caching, or explicitly document single-process support.
- [ ] Define Pydantic models for a versioned YAML rule schema and validate rules at load/deploy time.
- [ ] Migrate Fashion rules into generic rule primitives while retaining the existing Python validator as a compatibility adapter.
- [ ] Add PostgreSQL integration coverage and repository transaction/error tests.

## P1 — Prepare extensibility without overbuilding

- [ ] Define stable plugin manifests for validators, extractors, mappers, and exporters, including name, version, and capabilities.
- [ ] Create category manifests so classification signals, rules, and extraction vocabulary are not spread across modules.
- [ ] Make unknown/tied category classification explicit (`Unknown` or review required) instead of choosing by ordering.
- [ ] Move home-appliance vocabulary into versioned data/config assets and add precision/recall fixtures.
- [ ] Add deterministic file-inspection and schema-detection contracts before implementing further agents.
- [ ] Design a persisted, allowlisted workflow-plan format before autonomous-agent behavior.

## P2 — API, dashboard, and reports

- [ ] Version API routes and add typed schemas, error envelopes, pagination, and OpenAPI examples.
- [ ] Add target capabilities incrementally: upload/inspect, clean, extract, mapping, rules, and chat; each must be a separate application use case.
- [ ] Make Streamlit consume the API or a dedicated application facade instead of rebuilding services directly.
- [ ] Add execution progress, logs, health-score charts, report downloads, and user-facing failures to the dashboard.
- [ ] Expand reports with field-level metrics, charts, explainable remediation, and CSV export.
- [ ] Add delivery adapters for local/API/S3/Google Drive exports with isolated credentials and audit events.

## P2 — Quality and operations

- [ ] Add Ruff, Black, mypy/pyright, pre-commit, coverage thresholds, and CI jobs for lint/type/test/security checks.
- [ ] Reformat compressed one-line code only when touching a file; do not perform a repository-wide formatting rewrite without a dedicated change.
- [ ] Add structured logs with request/execution/user correlation IDs and redaction rules.
- [ ] Configure OpenTelemetry exporters, custom spans, metrics, alerts, sampling, and retention policy.
- [ ] Add LLM timeouts, retries, provider abstraction, structured outputs, redaction, prompt/version capture, and evaluation datasets.
- [ ] Add load, failure-recovery, and end-to-end tests for multi-file and batch execution.

## Deferred until the core is stable

- [ ] JSON, XML, HTML, and PDF ingestion.
- [ ] Fuzzy and semantic duplicate detection.
- [ ] RAG-backed rule retrieval and user preferences/memory.
- [ ] Third-party plugin installation and distribution.
- [ ] React dashboard.
