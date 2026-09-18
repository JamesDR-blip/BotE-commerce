# CHANGELOG

## S22 — AI Copilot for Data Operations

**Status:** COMPLETE

### Summary

S22 introduces the governed conversational AI Copilot for dataset inspection, data-health diagnosis, workflow authoring, simulation, and workflow execution.

### Delivered

- Added `application/copilot/` application boundary.
- Added provider-facing `CopilotAgent`.
- Added typed Copilot contracts, tool definitions, and tool registry.
- Added eight registered Copilot tools:
  - `list_datasets`
  - `get_dataset`
  - `get_health`
  - `get_diagnostics`
  - `get_remediation_proposals`
  - `author_workflow`
  - `simulate_workflow`
  - `execute_workflow`
- Reused RequirementAgent and PlannerAgent for natural-language workflow authoring.
- Reused existing Workflow Runtime for execution.
- Added owner-scoped process-local Copilot sessions.
- Added FastAPI SSE streaming.
- Added Streamlit Copilot UI and dashboard client support.
- Added safe approval metadata presentation without exposing approval tokens or token hashes.

### Architecture / Security

- Copilot tools are restricted to registered platform capabilities.
- No arbitrary SQL, Python, shell, `eval`, or `exec` capability was introduced.
- Copilot does not bypass the existing ChangeSet, risk, approval, lineage, audit, or channel-sync boundaries.
- Existing authentication and authorization boundaries remain authoritative.
- No new database schema or Alembic migration was required.

### Database

S22 adds no migration.

Current Alembic revision/head:

`20260916_03`

Latest migrations remain the S21 channel synchronization migrations:

- `database/migrations/versions/20260916_01_add_channels.py`
- `database/migrations/versions/20260916_02_add_sync_jobs.py`
- `database/migrations/versions/20260916_03_add_channel_mappings.py`

### Verification

- Full regression: **779 passed, 1 warning**.
- S22 focused coverage: **37 passed, 1 warning**.
- Broader S22 regression subset: **103 passed, 1 warning**.
- `python -m compileall`: PASS.
- Alembic current/head: `20260916_03`.
- Single Alembic head confirmed.

### Known Boundaries

- Copilot sessions remain process-local.
- Existing seven Alembic model/schema drift operations remain.
- Existing Starlette/AnyIO TestClient deprecation warning remains.
- Existing deferred S21 channel integration work remains outside S22.

---
## S21 — Channel Sync & Multi-Platform Connectors — COMPLETE

### Summary

S21 adds the first governed external-channel synchronization layer while preserving the existing internal production mutation boundary.

### Delivered

- CanonicalProduct and ChannelMapping domain contracts.
- Channel, SyncJob, SyncAttempt and Connector contracts.
- Deterministic canonical-product projection.
- Idempotent sync jobs.
- Create/update/noop delta handling using deterministic hashes.
- Channel mapping persistence and reconciliation.
- Encrypted channel credentials with fail-closed behavior.
- Bounded HTTP retry/backoff.
- Shopify connector.
- Amazon SP-API connector.
- Channel synchronization API.
- Owner/workspace-scoped repository access.

### Security

- Credentials are encrypted at rest.
- Credentials are excluded from API responses.
- Missing encryption configuration fails closed.
- No plaintext fallback.
- No unsafe eval/exec, unsafe YAML, or arbitrary SQL path was introduced.

### Database

S21 migrations:

- `20260916_01_add_channels.py`
- `20260916_02_add_sync_jobs.py`
- `20260916_03_add_channel_mappings.py`

Repository Alembic head: `20260916_03`.

### Architecture Decisions

1. Preserve ChangeSet as the only internal production dataset mutation boundary.
2. Treat external channel operations as a separate external side-effect boundary.
3. Reuse existing dataset, storage, mapping and normalization abstractions for canonical projection.
4. Keep channel contracts in Domain, orchestration in Application, and external API adapters in Infrastructure.
5. Use injected credential encryption and fail closed when encryption is unavailable.
6. Enforce sync idempotency in both application logic and database constraints.
7. Use deterministic product hashes for delta/noop decisions.
8. Implement Shopify and Amazon SP-API according to S21 verification scope.
9. Do not fabricate Amazon SigV4 signing; production-grade signing remains deferred.
10. Keep unsupported channel adapters explicit rather than introducing unsafe placeholders.

### Verification

- Full regression: **706 passed, 1 warning**.
- S21 targeted coverage: **57 passed**.
- S21 API coverage: **11 passed, 1 warning**.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Alembic current/head: `20260916_03`.

### Deferred Work

- TikTok Shop connector.
- Shopee connector.
- Lazada connector.
- Production-grade Amazon SP-API SigV4 authentication/signing.
- Dedicated distributed/channel-specific rate limiting.
- Durable asynchronous channel workers.
- Cross-product external compensation/reconciliation.

---

## S20 — Autonomous Agent Operations — COMPLETE

Implemented the governed autonomous operations loop on top of the existing S18 ChangeSet and S19 lineage/audit boundaries.

### Added

- Added AutonomousPolicy domain contract with hard limits for operations, iterations, affected rows, ChangeSet items, blast radius, and consecutive failures.
- Added AutonomousDecision and AutonomousEvaluation domain contracts.
- Added AutonomousOpsService for deterministic autonomous governance.
- Added AutonomousOperationsOrchestrator.
- Connected existing DataHealthService, requirements, PlannerAgent, RiskService, SimulationService, ChangeSet services, ApprovalService, WorkflowAuthoringService, WorkflowExecutionRepository, and AgentMemoryService.
- Added closed-loop Detect -> Diagnose -> Plan -> Simulate -> Risk -> Prepare ChangeSet -> Approve/Apply -> Verify -> Learn orchestration.
- Added low-risk autonomous ChangeSet Apply path.
- Added high/critical-risk approval routing.
- Added fail-closed guardrails for excessive blast radius, affected rows, ChangeSet items, operations, iterations, and consecutive failures.
- Added failed execution persistence for blocked autonomous operations.
- Added post-Apply verification of dataset identity, storage key, and content hash.
- Added execution learning after successful verified autonomous Apply.
- Added targeted unit and integration coverage.
- Wired the autonomous orchestrator through services/container.py.

### Architectural Decisions

- Keep ChangeSet as the only production mutation boundary.
- Do not introduce a second planner, risk engine, approval service, verification service, or workflow engine; reuse existing application/execution abstractions.
- Keep autonomous governance in the application layer and hard policy contracts in the domain layer.
- Separate RiskService classification from autonomous hard guardrails.
- Do not invoke capabilities directly from the autonomous orchestrator.
- Use existing ChangeSet preparation, transactional Apply, Rollback, Approval, Lineage, and Audit boundaries.
- Treat invalid or missing blast-radius data as unsafe for autonomous Apply.
- Keep streaming autonomous mutation fail-closed because the existing ChangeSet preparation path does not support streaming.

### Security / Safety

- Autonomous execution is bounded by explicit operation, iteration, row, ChangeSet-item, blast-radius, and consecutive-failure ceilings.
- High/Critical risk actions do not auto-apply and instead create approval requests.
- Blocked operations fail closed and do not mutate production datasets.
- Production mutations continue to emit the existing transactional audit events.
- No direct capability or dataset mutation path was introduced.

### Verification

- Full regression: **638 passed**.
- Latest full-suite runtime: **27.56 seconds**.
- python -m compileall -q .: passed.
- git diff --check: passed.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- No new Alembic migration was required.
- Repository Alembic head remains 20260914_03.

### Known Scope Boundaries

- Streaming autonomous ChangeSet preparation is unsupported and fails closed.
- Autonomous policy is currently instantiated in the composition root because no existing autonomous-policy configuration mechanism was available.
- Simulation-derived affected-row and ChangeSet-item metrics require available simulation metadata; broader guardrail telemetry remains future hardening work.
- Seven pre-existing Alembic model/schema drift operations remain outside S20 scope.

---
## S19 — Data Lineage & Audit Trail — COMPLETE

Implemented end-to-end capability-level lineage tracking and a workspace-scoped tamper-evident audit trail on top of the S18 ChangeSet mutation boundary.

### Added

- Added DataLineageEvent domain model.
- Added AuditEvent domain model.
- Added canonical SHA-256 audit event hashing.
- Added DataLineageEventRepository.
- Added AuditEventRepository.
- Added LineageTrackingService.
- Added AuditService.
- Added automatic lineage emission after successful capability execution.
- Added ordered capability lineage chaining through previous_event_id.
- Added owner-scoped GET /datasets/{dataset_id}/lineage.
- Added owner-scoped and filtered GET /audit-logs.
- Added sensitive audit metadata sanitization.
- Added audit events for ChangeSet Apply.
- Added audit events for ChangeSet Rollback.
- Added audit events for approved ChangeSet application.
- Added transactionally consistent audit writes for production mutations.
- Added Alembic migration 20260914_03_add_lineage_audit.py.
- Wired lineage and audit services through the composition root.
- Added regression and integration coverage.

### Architectural Decisions

- Keep ExecutionTrace as execution telemetry; do not repurpose it as lineage or audit persistence.
- Keep lineage and audit domain models framework-independent.
- Keep lineage/audit orchestration in application services.
- Keep persistence concerns behind repository adapters.
- Emit lineage from capability execution through an optional callback so existing callers remain compatible.
- Keep ChangeSet as the only production mutation boundary.
- Record mutation audit events in the same transaction as ChangeSet Apply, Rollback, and Approval Apply.
- Scope externally exposed lineage and audit queries to the authenticated owner's resources.
- Treat the audit chain as tamper-evident rather than absolutely tamper-proof.

### Security

- Audit metadata is sanitized for credentials, tokens, passwords, secrets, cookies, and related sensitive values.
- Raw dataset/customer secrets are not intentionally persisted into audit payloads.
- Hash chaining uses SHA-256 over a canonical event representation.
- Workspace serialization prevents concurrent writers from producing inconsistent chain heads.

### Verification

- Full regression: **612 passed**.
- Latest full-suite runtime: **26.65 seconds**.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- git diff --check: no whitespace errors; only Git LF/CRLF normalization warnings remain.
- S19 API, repository, lineage, audit, ChangeSet, approval, rollback, and workflow integration coverage passes.

### Migration

- 20260914_03_add_lineage_audit.py
- Creates data_lineage_events.
- Creates audit_events.
- Adds indexed ownership/execution/workflow/resource fields.
- Adds unique SHA-256 event_hash.

### Known Scope Boundaries

- Artifact-level lineage using storage keys and content hashes is deferred.
- Retention enforcement according to governance policy is deferred.
- Seven pre-existing Alembic model/schema drift operations remain outside S19 scope.

---
## S18 — ChangeSet & Atomic Rollback Engine — COMPLETE

Implemented the immutable production mutation boundary required for autonomous data operations.

### Added

- Added immutable `ChangeSet` aggregate and `ChangeSetItem`.
- Added `PREPARED`, `APPLIED`, and `ROLLED_BACK` lifecycle states.
- Added candidate after-artifact materialization with SHA-256 verification.
- Added `ChangeSetRepository`.
- Added transactional ChangeSet Apply.
- Added transactional ChangeSet Rollback.
- Added optimistic concurrency protection using dataset storage-key guards.
- Added owner-scoped ChangeSet query APIs.
- Added ChangeSet list/detail/rollback endpoints.
- Added approval → ChangeSet foreign-key integrity.
- Added `ApprovalChangeSetService`.
- Integrated candidate ChangeSet preparation into the high/critical risk approval path.
- Changed approved ChangeSet-backed executions from queue resumption to atomic ChangeSet application.
- Added execution completion in the same transaction as approval and ChangeSet application.

### Architectural Decisions

- `WorkflowEngine` remains responsible for computation/execution, not production persistence.
- `ChangeSet` is the only production mutation boundary.
- Dataset artifacts are immutable; production state is represented by the `DatasetRecord.storage_key` pointer.
- Candidate after-artifacts are materialized before HITL approval.
- Approval operates on a concrete immutable ChangeSet rather than re-executing a workflow.
- Apply and Rollback use optimistic concurrency guards and atomic database transactions.
- ChangeSet items contain logical row-level before/after snapshots; complete dataset artifacts remain in immutable storage.
- Approved ChangeSet-backed executions do not return to the existing execution queue.

### Verification

- Full regression: **591 passed**.
- Runtime: **28.05 seconds**.
- `python -m compileall` passed.
- One existing Starlette/AnyIO TestClient deprecation warning remains.
- Alembic current/head: `20260914_02`.
- S18 migrations:
  - `20260914_01_add_changesets.py`
  - `20260914_02_add_approval_changeset_fk.py`
- `aAlembic check` still reports seven pre-existing model/schema drift operations unrelated to S18.

### Known Scope Boundaries

- Streaming ChangeSet candidate materialization remains future work; the current ChangeSet preparation path explicitly rejects streaming execution mode.
- Row-level ChangeSet identity currently follows S17 positional row alignment rather than a business-key identity model.
- The in-process workflow queue remains non-durable.
- The existing Starlette/AnyIO dependency warning remains.
- Seven pre-existing Alembic model/schema drift operations remain outside S18 scope.

## S17 — Shadow Mode / Simulation — COMPLETE

Implemented an isolated workflow simulation path for safe dry-run verification without production mutation.

### Added

- Added domain simulation contracts:
  - SimulationResult
  - DiffPreview
  - TabularDiff
  - RowDiff
- Added ShadowExecutionRunner for ephemeral workflow simulation.
- Added SimulationService with owner-scoped workflow and dataset resolution.
- Added POST /workflows/{workflow_id}/simulate.
- Added workflow/dataset project-scope validation.
- Added read-only streaming simulation through DatasetStorage.open().
- Added bounded-memory streaming diff aggregation.
- Added deep isolation of DataFrame, Series, and mutable auxiliary inputs.
- Added simulation result and diff API response schemas.
- Added regression coverage for zero production mutation and input isolation.

### Architectural Decisions

- Reuse the existing CapabilityExecutionService and capability registry rather than introducing a second capability execution engine.
- Keep simulation orchestration in the execution/application layers; keep simulation result contracts in the domain layer.
- Keep the production WorkflowEngine execution path unchanged.
- Simulation must not create or persist WorkflowExecution records.
- Simulation must not persist execution traces or write dataset storage.
- Simulation must not create ChangeSets or mutate production state.
- Preserve S16 Risk & Approval boundaries; simulation does not bypass approval controls.
- Use bounded-memory accumulation for streaming diffs rather than materializing the complete dataset.

### Verification

- Full regression: 546 passed.
- Full suite runtime: approximately 25.01 seconds.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- git diff --check clean.
- No Alembic migration required.

### Known Scope Boundaries

- Streaming row diffs currently use positional row alignment rather than business-key matching.
- The simulation diff preview is bounded by max_diff_rows; the API currently uses the default limit.
- Simulation plan deserialization is currently local to SimulationService.
- The existing Starlette/AnyIO dependency warning remains.

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
- Keep persistence behind rrepositories/infrastructure adapters.
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
- Keep diagnostics sanitized at the aapplication/API boundary.
- Keep remediation proposals read-only until later approval/ChangeSet infrastructure exists.
- Do not invent a timeliness score without a reliable freshness signal.
- Preserve existing project ownership boundaries rather than introducing a new workspace-wide health API.
- Preserve existing Clean Architecture + DDD layering.

### Verification

- Full regression: `510 passed`.
- Full suite runtime: approximately `24.5 seconds`.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- Alembic current/head: `f3a4b5c6d7e8`.
- `git diff --check`: no whitespace errors; existing LF/CRLF conversion warning remains for `ttests/test_persistence.py`.

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
Formalize package layering into `domain/`, `aapplication/`, `execution/`, and `infrastructure/`, and extract domain serialization helpers.

**Reason:**
1. Group use-case services under `aapplication/` (`workspace`, `datasets`, `workflows`, `quality`).
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
