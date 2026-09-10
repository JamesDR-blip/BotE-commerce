# Architecture Audit

**Scope:** source-code and configuration review, 30 July 2026. This is a documentation-only audit; it does not modify application code.

## Executive summary

The repository is a compact, working data-quality application. It accepts a tabular upload through FastAPI, classifies the dataset into one of three categories, applies deterministic validation and auto-fixes, calculates a health score, creates reports, and persists execution history through SQLAlchemy. It already has valuable architectural seams: an application factory, a composition root, repositories, category validators, YAML rule content, and a text-only LLM adapter.

It is not yet a general-purpose AI Data Studio capable of dynamically planning workflows. Current `agents` are synchronous orchestration classes, not autonomous agents, and validation is the only implemented workflow. The most valuable next work is to make the existing workflow safe and consistent across entry points, then introduce reusable workflow contracts before adding new capabilities.

## Current architecture

```text
FastAPI / Streamlit
  |                 \
  |                  \--> Dashboard constructs Container directly
  v
Container (composition root)
  ├── TabularUploadReader (FastAPI route only)
  ├── QualityService
  │     ├── classifier -> rules -> autofix -> validate -> QA/anomaly detection
  │     ├── report generator
  │     └── execution repository + in-memory cache
  ├── ValidatorRegistry (discovers validators package)
  └── optional Gemini text assistant
       |
       +--> SQLite locally / PostgreSQL through Docker Compose
```

| Area | Current responsibility | Assessment |
|---|---|---|
| `api/main.py` | Application factory, HTTP endpoints, upload-to-service adapter | Thin enough currently; route names do not match the target API. |
| `services/container.py` | Builds dependencies | A sound composition root; it eagerly creates schemas and plugins. |
| `services/quality_service.py` | Validation use-case orchestration | Clear application service, but coupled to one fixed workflow. |
| `agents/workflow.py` | Classify, retrieve rules, auto-fix, validate, QA | Useful decomposition, but not multi-agent planning. |
| `validators/` | Category-specific normalization and checks | Validator discovery works; executable rules are mainly hard-coded in Python. |
| `repositories/`, `models/database.py` | SQLAlchemy persistence | Execution/report/log history exists; no migrations, user/tenant/workflow model, or retention policy. |
| `reports/generator.py` | Excel, JSON, HTML, PDF output | Functional but minimal, synchronous, and local-filesystem-only. |
| `dashboard.py` | Streamlit UI | Prototype UI that duplicates parsing and dependency construction. |

## Strengths

- The application factory and explicit `Container` avoid mutable module-global services in the API path.
- Validators are dynamically discovered and share a small abstract interface.
- LLM output is text-only and is never executed as code.
- Executions, validation logs, and report locations are persisted behind a repository layer.
- The cache key includes source bytes, category, and rule version.
- The FastAPI path has a dedicated upload boundary with extension checks, path-like filename rejection, size configuration, and spreadsheet-formula escaping.
- Docker, Compose, and a basic GitHub Actions test workflow already exist.

## Technical debt and design gaps

### P0 — Security, data exposure, and operational correctness

1. **The dashboard bypasses the secure upload reader.** `dashboard.py` parses uploads directly with pandas. It has no configured size limit and does not apply formula escaping, producing inconsistent behavior and restoring spreadsheet-formula-injection risk.
2. **There is no authentication or authorization.** Any reachable caller can list executions and download reports. An execution ID is not an authorization boundary.
3. **The size limit is checked after buffering the whole request.** `await file.read()` runs before `TabularUploadReader` can reject oversized content. Production also needs upstream request limits and streamed ingestion.
4. **Report retrieval trusts database paths.** The API serves a path returned by the database without confirming it stays below the configured report root. A compromised or manually altered record could expose arbitrary files.
5. **Production defaults are unsafe.** Compose contains a committed PostgreSQL password and lacks secret injection, TLS/reverse-proxy guidance, health checks, resource limits, and production deployment configuration.

### P1 — Scalability and reliability

1. **Database schemas use `create_all`, not migrations.** Schema changes cannot be versioned, reviewed, or safely deployed across environments.
2. **Processing is synchronous and in-process.** File parsing, auto-fix, anomaly detection, LLM calls, reports, and database writes run in one request and will consume web workers on large datasets.
3. **Dataframes and reports are entirely memory/local-disk based.** There is no chunked ingestion, object-storage abstraction, artifact lifecycle, or retention cleanup.
4. **The cache is unbounded and per process.** `TTLCache` is not shared between workers and cached report paths can outlive removed artifacts.
5. **Threaded validation uses a fixed four-way split.** Parallelism and error behavior are not explicitly modeled; pandas workloads may not benefit from threads.
6. **The LLM adapter lacks timeout, retry, circuit breaker, tracing, prompt/version recording, and structured-output validation.** It also creates a provider client per call.

### P1 — Domain and extensibility

1. **“Rules from YAML” is not a rule engine yet.** YAML stores human-readable descriptions; fields, regexes, severities, and fixes remain in Python validators.
2. **The plugin system registers validators only.** It lacks manifests, versions, dependencies, mappings, extractors, exporters, and a stable third-party contract.
3. **Category classification is hard-coded.** `ClassifierAgent` contains categories, signals, and appliance terms. New categories require code changes, and ties may silently select the first category.
4. **Title extraction has hard-coded vocabulary.** Brands, products, materials, colors, and patterns are embedded in one Python module.
5. **Most target capabilities are absent.** There is no planner, requirement detector, inspector for JSON/XML/HTML/PDF, schema detector, mapping, duplicate, delivery, memory, or report-planning agent.
6. **No workflow state model exists.** Workflow definitions, step status, retries, input/output artifacts, and independent job IDs are not persisted.

### P2 — API, maintainability, observability, and tests

1. The existing API provides `/validations`, `/categories`, and `/executions`, not the requested `/upload`, `/clean`, `/extract`, `/mapping`, `/history`, `/report/{id}`, `/rules`, and `/chat` capabilities.
2. Request/response contracts are sparse: query and upload constraints are inline, history returns dictionaries, and there is no stable error envelope, pagination metadata, or API versioning.
3. The dashboard constructs dependencies, parses files, and invokes the application service directly rather than using an API or shared facade.
4. Logs lack request/execution/user correlation IDs. OpenTelemetry is optional instrumentation only, with no exporter configuration, custom spans, metrics, audit-event model, or data-privacy policy.
5. Tests cover basic endpoint, validator, title-extraction, and upload-reader behavior, but not authorization, malformed spreadsheets, rule failures, report-path containment, PostgreSQL, concurrency, LLM failures, or dashboard flow.
6. Formatting is inconsistent; several modules compress multiple statements onto one line. Ruff, Black, type checking, and pre-commit configuration are absent.
7. `Base.metadata.create_all` during application construction creates infrastructure side effects at startup and in tests; this belongs to migration/bootstrap operations.

## Duplicated or diverging logic

| Concern | Locations | Consequence | Recommended consolidation |
|---|---|---|---|
| CSV/Excel parsing | `api/main.py`, `dashboard.py` | Different safety and error behavior | Use one ingestion service at every entry point. |
| Dependency construction | `api/main.py`, `dashboard.py` | Separate lifecycles and harder tests | Use lifespan-managed services; make dashboard call API or a shared facade. |
| Required-field/value checks | Validators and prose YAML | Documentation can drift from execution | Use typed YAML rules with reusable validator primitives. |
| Category knowledge | Classifier, validators, rules YAML, title extractor | Adding a category requires many edits | Introduce a category/plugin manifest. |
| Report access and metadata | Generator, repository, API | No artifact integrity policy | Add an `ArtifactStore` abstraction and path-containment checks. |

## Unsafe boundaries to preserve

- Never treat a client filename as a filesystem path.
- Treat all spreadsheet cells as untrusted at export time; formula escaping must apply to every ingestion/export path.
- Resolve authorized artifact IDs to paths validated under the artifact root; never expose persisted paths directly.
- Keep LLM calls out of critical synchronous requests; minimize/redact evidence, bound timeouts/retries, and validate structured output.
- Continue using `yaml.safe_load`, then validate the parsed result with a typed schema before activation.
- Dynamic plugin discovery imports code. Keep plugins reviewed and allowlisted; add distribution trust controls before supporting third parties.

## Incremental migration roadmap

### Phase 0 — Baseline and guardrails (P0)

1. Make every upload path use one ingestion service; enforce upstream size limits and add malicious-file tests.
2. Add authentication, user/tenant ownership, authorization for history/artifacts, and report-root containment.
3. Move secrets to environment variables or a secret store; remove development credentials from deployment defaults.
4. Add formatter, linter, type checker, and pre-commit checks to CI.

**Exit criteria:** no unauthenticated artifact access, identical upload safety at every entry point, and repeatable CI.

### Phase 1 — Reliable validation platform (P1)

1. Introduce Alembic migrations and separate SQLite development from PostgreSQL production configuration.
2. Create typed application commands/results for ingestion, validation, history, and artifact retrieval; keep HTTP routes as adapters.
3. Introduce a persisted job/execution state machine and background worker queue.
4. Add `ArtifactStore` implementations for local storage first and S3-compatible storage later, including retention and cleanup.
5. Define a typed, versioned YAML rule schema and generic rule evaluators; migrate one category at a time with validator compatibility.

**Exit criteria:** queued executions can be retried and observed, rules are validated/versioned independently, and database changes run through migrations.

### Phase 2 — Extensible workflows and plugins (P1)

1. Define plugin manifests/interfaces for validators, extractors, mappings, and exporters.
2. Add category manifests to remove hard-coded classifier and extractor knowledge.
3. Add a deterministic, allowlisted workflow planner that maps typed requests to registered capabilities and persists the plan.
4. Add file inspection and schema detection before adding cleaning, extraction, mapping, and duplicate-detection steps.

**Exit criteria:** a category/platform can be added through a plugin/configuration, and workflows have persisted step-level state.

### Phase 3 — AI-assisted Data Studio (P2)

1. Add provider-agnostic LLM ports with structured outputs, redaction/safety policy, observability, evaluation fixtures, and human-review thresholds.
2. Limit LLM use to ambiguous classification, explanations, fix suggestions, extraction, and schema mapping; deterministic validation remains authoritative.
3. Build report summaries/charts and dashboard/API job progress on persisted executions.
4. Add optional local/API/S3/Google Drive delivery adapters with credential isolation and audit logging.

**Exit criteria:** AI assistance is measurable and recoverable, never executes generated code, and cannot bypass deterministic guardrails.

## Recommended next implementation slice

Start with **unified ingestion and protected artifact access**: move Streamlit to the shared reader, add a report-artifact resolver that validates the reports root, and write regression tests. Do not add new agents or endpoints until this common boundary is stable.

---

## Post-Audit Implementation Status (September 2026 Addendum)

The recommendations and phased roadmap from this audit have been systematically addressed across subsequent sprints:

1. **Unified Secure Ingestion (Phase 0 - P0 resolved):**
   - `TabularUploadReader` (`infrastructure/upload/tabular_reader.py`) serves as the single safe boundary for CSV, XLS, and XLSX file ingestion.
   - Enforces `MAX_UPLOAD_BYTES`, rejects path-like filenames, and escapes spreadsheet formulas (`=`, `+`, `-`, `@`) to prevent CSV injection.
   - Streamlit dashboard (`app/dashboard.py`) communicates strictly over HTTP via `app/api_client.py` and no longer parses raw uploads or constructs database sessions directly.

2. **Persistence & Migrations (Phase 1 - P1 resolved):**
   - Introduced Alembic migrations (`database/migrations/`).
   - Current migration head: `b05fd7d45c87` (`b05fd7d45c87_enforce_workspace_ownership.py`).
   - Full persistence for Workspaces, Projects, Datasets, Workflows, WorkflowVersions, Executions, and Traces behind repository boundaries.

3. **Clean Architecture & DDD Decomposition (Phase 2 - P1 resolved):**
   - **`domain/`**: Pure business models, contracts, and validation/catalog/quality domain services.
   - **`application/`**: Use-case orchestration services (`WorkspaceProjectService`, `DatasetService`, `DatasetIngestionService`, `QualityService`, `WorkflowRuntimeService`).
   - **`execution/`**: `WorkflowEngine`, `CapabilityExecutionService`, and `ExecutionTraceCollector` for reliable pipeline execution.
   - **`infrastructure/`**: Isolated cache (`TTLCache`), logging, persistence, and ingestion adapters.

4. **Extensible Capabilities & Safe Rule Engine (Phase 2 - P1 resolved):**
   - `CapabilityRegistry` allows dynamic discovery and dependency-ordered execution of capabilities (`Cleaning`, `Normalization`, `Extraction`, `Validation`, `QA`).
   - `rule_engine` parses and evaluates declarative YAML rules without arbitrary code execution.
   - `plugins.registry.ValidatorRegistry` supports dynamic plugin discovery.

5. **Test Harness & Operational Stability:**
   - 396 automated unit and integration tests passing (`396 passed in ~4.4s`).
   - Structured JSON logging implemented via `StructuredJsonFormatter`.
