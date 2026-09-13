# CHANGELOG

## S16 — Risk & Approval Engine — COMPLETE

Implemented the Risk & Approval Engine as a policy-driven human-in-the-loop safety boundary for workflow execution.

### Added

- Added `RiskPolicy` with deterministic `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL` classification.
- Added `ConfidenceScore` validation.
- Added risk evaluation application service.
- Added persisted risk assessments.
- Added `ApprovalRequest` and `ApprovalDecision`.
- Added `PENDING_APPROVAL` and `CANCELLED` workflow execution states.
- Added approval-aware workflow runtime integration.
- Added approval release back to the existing queue/worker execution path.
- Added rejection cancellation.
- Added secure approval-token generation and SHA-256 token-hash persistence.
- Added approver-role authorization.
- Added approval token validation and expiry handling.
- Added risk and approval API routes.
- Wired `DataHealthService` confidence into the production runtime.
- Added S16 domain, application, persistence, API, and runtime regression coverage.

### Architectural Decisions

- Keep risk policy and value objects in the framework-independent domain layer.
- Keep risk/approval orchestration in application services.
- Keep persistence behind repositories/infrastructure adapters.
- Do not bypass the existing workflow execution state machine or queue boundary.
- High/Critical risk executions remain blocked until explicit approval.
- Approval tokens are never persisted in plaintext and are not exposed by pending-approval listings.
- Preserve existing synchronous workflow behavior and legacy runtime compatibility.
- Do not introduce ChangeSet/rollback implementation as part of S16; that remains a later sprint boundary.

### Verification

- Full regression: `533 passed`.
- Full suite runtime: approximately `25.55 seconds`.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- Repository Alembic head: `20230912_04`.
- Local database revision: `c13a7e91d204`.

### Known Scope Boundaries

- Blast radius is currently supplied through execution-plan risk metadata.
- Approval request creation and runtime risk assessment are currently separate lifecycle steps.
- The in-process queue remains non-durable.
- Existing Alembic baseline/bootstrap limitations remain outside S16 scope.


## S15 — Data Health Command Center — COMPLETE

Implemented the Data Health Command Center on top of the existing dataset, validation, persistence, and dashboard architecture.

### Added

- Added multidimensional health domain model:
  - Completeness
  - Validity
  - Uniqueness
  - Consistency
  - Timeliness
- Added assessed/unassessed health dimensions and aggregate scoring.
- Added sanitized issue diagnostics.
- Added read-only remediation proposals.
- Added `DataHealthService`.
- Added project-scoped dataset health aggregation.
- Added `GET /health-metrics`.
- Added `GET /diagnostics/{dataset_id}`.
- Added ownership-scoped diagnostic access.
- Added validation-log aggregation without exposing raw rows or row numbers.
- Added Data Health dashboard views.
- Added remediation preview with no mutation execution.
- Added persisted `executions.dataset_id` relationship and Alembic migration.
- Added domain, application, API, dashboard-client, and persistence regression coverage.

### Architectural Decisions

- Reuse persisted dataset profile metadata rather than introducing a second profiling system.
- Reuse existing validation execution health scores for validity.
- Keep diagnostics sanitized at the application/API boundary.
- Keep remediation proposals read-only until later approval/ChangeSet infrastructure exists.
- Do not invent a timeliness score without a reliable freshness signal.
- Preserve existing project ownership boundaries rather than introducing a new workspace-wide health API.
- Preserve existing Clean Architecture + DDD layering.

### Verification

- Full regression: `510 passed`.
- Full suite runtime: approximately `24.5 seconds`.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- Alembic current/head: `f3a4b5c6d7e8`.
- `git diff --check`: no whitespace errors; existing LF/CRLF conversion warning remains for `tests/test_persistence.py`.

### Known Scope Boundaries

- Historical multidimensional health snapshots are not persisted.
- Category benchmark computation is not implemented.
- Remediation proposals are preview-only and are not persisted as an approval/execution lifecycle.
- Timeliness remains unassessed without a reliable freshness/SLA signal.

## S14-B — Streaming / Chunked Workflow Execution — COMPLETE

Implemented scalable tabular workflow execution on top of the existing S14-A asynchronous execution foundation.

### Added

- Added optional persisted `dataset_id` to workflow executions.
- Added dataset ownership and workflow-project scope validation.
- Added Alembic migration `e2f3a4b5c6d7`.
- Extended `WorkflowEngine` with opt-in streaming execution.
- Reused the existing `DatasetStorage` and `StreamingTabularReader`.
- Processed persisted CSV/XLSX sources chunk-by-chunk.
- Reused the existing capability execution pipeline for each chunk.
- Preserved the existing synchronous execution path.
- Preserved the S14-A execution-ID-only queue contract.
- Added 100k-row streaming benchmark coverage.

### Architectural Decisions

- Reuse `WorkflowEngine`; no separate streaming execution engine.
- Reuse existing capability execution instead of introducing a parallel batch-capability framework.
- Persist dataset identity before asynchronous dispatch rather than placing file/data payloads on the queue.
- Keep `dataset_id` nullable for backward compatibility.
- Use existing execution-plan metadata as the opt-in streaming mode boundary.
- Do not introduce a durable/distributed queue as part of S14-B.

### Verification

- S14-B targeted regression: `47 passed`.
- Full regression: `495 passed`.
- Full suite runtime: approximately `24.8 seconds`.
- 1 existing Starlette/AnyIO deprecation warning remains.
- 100k-row benchmark: 100,000 rows processed in 10 chunks of 10,000 rows.
- Memory assertion uses `tracemalloc` Python-allocation measurements rather than OS RSS.

### Migration

- `e2f3a4b5c6d7_add_workflow_execution_dataset.py`
- Adds nullable `workflow_executions.dataset_id`.
- Adds foreign key to `datasets.id`.
- Adds index `ix_workflow_executions_dataset_id`.

## S14-A — Asynchronous Workflow Execution

Added asynchronous workflow execution using a minimal in-process queue.

Changes:
- Added QUEUED workflow execution state.
- Added atomic workflow execution claiming.
- Added workflow execution queue application port.
- Added in-process FIFO queue infrastructure adapter.
- Added WorkflowExecutionWorker.
- Added persisted-execution async execution path.
- Added async execution and status API endpoints.
- Added API, worker, queue, repository, runtime, and state contract tests.

Architecture:
- Queue payloads contain execution_id only.
- Worker reloads persisted execution state.
- Persisted workflow version is used for deterministic execution.
- Existing WorkflowEngine is reused.
- No separate async engine or external queue dependency was introduced.

Verification:
- 32 targeted S14-A tests passed.
- 484 full-suite tests passed.
- 1 existing Starlette/AnyIO deprecation warning remains.

## ADR-001

**Decision:**
Use Clean Architecture + Domain-Driven Design (DDD).

**Reason:**
Prevent framework and infrastructure coupling. Keep business rules and domain logic pure and independent from web frameworks (FastAPI/Streamlit) and ORMs (SQLAlchemy).

**Status:**
Accepted.

---

## ADR-002

**Decision:**
ChangeSet is the only production mutation boundary.

**Reason:**
Required for rollback, audit trails, data lineage, and human-in-the-loop approval gates.

**Status:**
Accepted.

---

## ADR-003

**Decision:**
Risk and Confidence are modeled as separate concepts.

**Reason:**
A highly confident automated action can still carry a high blast radius or business risk. Decoupling them allows nuanced approval policies.

**Status:**
Accepted.

---

## ADR-004

**Decision:**
Formalize package layering into `domain/`, `application/`, `execution/`, and `infrastructure/`, and extract domain serialization helpers.

**Reason:**
1. Group use-case services under `application/` (`workspace`, `datasets`, `workflows`, `quality`).
2. Centralize workflow runtime, state transitions, and capability dispatch under `execution/`.
3. Isolate caching behind an `application.cache.Cache` protocol with an infrastructure `TTLCache` implementation.
4. Provide pure domain serialization for `ExecutionPlan` and `WorkflowRequirement` under `domain/serialization/`.

**Status:**
Accepted and Implemented.

---

## ADR-005

**Decision:**
Introduce semantic rule retrieval behind a framework-independent `RuleRetriever` domain port, with Chroma isolated in the infrastructure layer.

**Reason:**
1. Enable context-aware rule discovery beyond static category lookup.
2. Keep Chroma, embeddings, and vector-store concerns outside the domain layer.
3. Preserve the existing deterministic `RuleRetrieverAgent.retrieve(category)` contract for executable validation.
4. Allow semantic retrieval to return typed, non-executable `SemanticRulePack` results.

**Status:**
Accepted and Implemented.

---

## ADR-006

**Decision:**
Keep semantic rule indexing explicit rather than synchronizing automatically during application startup.

**Reason:**
1. Avoid embedding-model loading and vector-store synchronization as startup side effects.
2. Keep YAML rule definitions as the authoritative source for parsing and versioning.
3. Make index synchronization an explicit application operation.
4. Allow stale vector-index entries to be removed during synchronization.

**Status:**
Accepted and Implemented.

---

## ADR-007

**Decision:**
Distinguish descriptive rule knowledge from executable validation rules in the semantic index.

**Reason:**
Semantic retrieval may return business guidance or descriptive rules that are useful for recommendation but must never become executable validation logic implicitly. Executable validation remains constrained to registered declarative primitives.

**Status:**
Accepted and Implemented.

---

## ADR-008

**Decision:**
Introduce tenant-scoped persistent agent memory behind an application service and repository boundary, with memory-derived corrections validated against capability contracts before affecting agent parameters.

**Reason:**
1. Enable agents to use prior user corrections and execution learning across sessions.
2. Enforce strict workspace/user tenant isolation at the persistence boundary.
3. Keep persistence concerns outside agents and the domain layer.
4. Prevent invalid or unknown memory values from introducing undeclared capability parameters.
5. Redact explicitly sensitive customer PII before memory persistence.
6. Preserve backward compatibility by making memory and tenant scope optional at existing agent interfaces.

**Status:**
Accepted and Implemented.