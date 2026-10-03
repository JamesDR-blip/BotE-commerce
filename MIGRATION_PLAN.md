# Migration Plan — Discovery Only

**Current-state note (final closure, 2026-10-02):** The migration-history descriptions and Phase 0–4 planning snapshots below predate the authorized Strategy D repair and final local validation. The active graph is a single baseline revision, `20261002_01`; the former 23 revisions remain archived at `database/migrations/archive/legacy_versions/`. PostgreSQL 16.15 fresh install and representative persistence Groups 1–7 passed on the disposable verification database, and the canonical suite passed 994/994 in 75.14 seconds. See [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md) and [`POSTGRESQL_16_VALIDATION_REPORT.md`](POSTGRESQL_16_VALIDATION_REPORT.md) for final evidence. Production schema/revision, backup/restore, production-equivalent upgrade rehearsal, and deployment order remain unverified; production migration authorization is not established.

**This is the finalized plan, not a record that implementation Phases 1–4 have run.** This documentation-only refresh changed no source, tests, migrations or runtime configuration. Phases 0–4 below define the evidence and controlled migration work to complete before Phase 5; no code migration was started. Order is checked against current imports, route wiring, named test modules, sprint records and the existing Alembic chain. Each change must be a bounded, reviewable slice.

## Baseline and constraints

- Git branch/status at start: `main`, no tracked/untracked source changes reported. Git printed permission warnings while scanning pre-existing pytest temporary directories; they were not opened or modified.
- Test scope: full `pytest -q` through the repository virtual environment (193 test modules discovered). Final run with temporary-directory access: **977 passed in 64.27 seconds**. Earlier sandboxed attempts could not enumerate temporary directories and raised `PermissionError`; they are environment failures, not counted as the baseline result. Record the exact environment/command before changing code so future results are comparable.
- Alembic: one reported head, `20260928_01`; no migration was applied during discovery.
- No PostgreSQL/Redis/Docker/provider-connected runtime validation was part of this baseline.
- Retain every existing API path, schema/output behavior, dataset handling, workflow status transitions, capability ordering/versions, approval and rollback semantics, risk decisions, lineage/audit records, channel sync effects, access scoping, and observability fields unless a concrete defect is separately accepted and recorded.
- Do not combine structural moves with domain/business behavior changes. Do not drop/rename persisted columns or rewrite migration history during consolidation.
- **Per-slice baseline gate:** before behavior-changing work, collect and pass the same 193 test modules / 977 tests; after each slice and before merge, require the same collection and 977 passed, with no new failures. Any intentional test-count change must be explained and reviewed. If the baseline cannot be reproduced, stop and resolve the environment/fixture issue before migration.
- The specific successful invocation recorded for this baseline was `.\venv\Scripts\python.exe -m pytest -q` (Windows PowerShell; 977 passed in 64.27 seconds). S28 records also report 977 passed, 3 warnings. This documentation refresh did not run tests again.
- Destination packages such as `application/ports/` are provisional proposals, not existing architecture. Prove the first target with concrete consumers and tests before creating or scaling it. No `src/platform` relocation is assumed.
- The complete app/API importer census and one-owner concept proposal are recorded in `DISCOVERY_REVIEW.md`; consult it before selecting a slice.

## Ordered migration phases

### Phase 0 — Stabilize evidence and guardrails

1. Preserve the accepted 977-pass result and capture test collection/command/environment. The evidence is in `ARCHITECTURE_INVENTORY.md`; the full suite is not rerun during this documentation-only refresh.
2. Use the file-level AST importer census in `DEPENDENCY_MAP.md`; before each actual slice, add call-site/runtime wiring (including `app.state.container`, dynamic plugin loading, dashboard and worker) for the exact target.
3. Reconcile README, `ARCHITECTURE_AUDIT.md`, S26-S28 sprint/handoff claims with code and named tests. Sprint notes are historical evidence, not proof of current runtime behavior.
4. Before code changes, add/confirm architecture dependency checks and public contract snapshots in CI; scope checks to package direction and exempt only documented composition roots.

**Exit gate:** repeatable 977-pass baseline with unchanged collection; named owner and consumer list for modules in the first migration slice; and tests that pin current API/storage/execution semantics.

**Rollback/recovery:** Phase 0 changes are discovery/guardrail work only. Revert any CI-only guardrail that blocks the known-good baseline, preserve the captured test report, and do not edit production code to make an unclassified baseline pass.

### Phase 1 — Draw application ports around active use cases

1. Start with `application/memory/memory_service.py -> repositories.agent_memory` as the first port experiment: it has a narrow direct dependency and named unit/repository/integration tests. Do not start with lineage until its complete API/audit consumer path is mapped.
2. Move authorization, compliance and quota contracts behind application-level abstractions because multiple application workflows consume `services.*` directly. Keep existing service classes/adapters as temporary shims.
3. Remove direct application imports of SQLAlchemy records, concrete repositories, Redis/Chroma/filesystem adapters, Google SDK and telemetry. Introduce only the ports needed by each use case.
4. Keep `services.container` as outer composition while considering whether to move its composition responsibility to one explicit outer composition module. Choose a target path only after runtime wiring and consumers are proven; do not introduce a `platform` package/tree to satisfy a naming target.

**Exit gate:** application use cases depend on domain and owned ports; service/repository implementation remains swappable in tests; runtime composition builds the same graph.

**Rollback/recovery:** migrate one use case per change. Keep the original service/repository constructor available as a compatibility adapter; if parity, security decisions, or the full 977-test gate fails, revert that slice and route composition back to the previous implementation. No schema change in this phase.

### Phase 2 — Route and persistence boundary cleanup

1. Migrate API routes that directly call repositories/container (`executions`, `channels`, `risk`) to application query/command services, preserving authorization and response schema.
2. Make route modules depend on API contracts and application interfaces; keep domain value types out of HTTP serialization internals where feasible.
3. Consolidate request/response schema ownership while preserving OpenAPI operation IDs, status codes, paths, field names and validation behavior.
4. Resolve `repositories.channels -> application.channels.credential_cipher` by moving the cipher contract to an outer-agnostic port and keeping cryptographic implementation in infrastructure.
5. Confirm migration/bootstrap ownership: tests may need an explicit schema fixture; deployment runs Alembic. Only then consider removing `Base.metadata.create_all` from session construction.

**Exit gate:** no route reaches a repository, ORM model or service container; Alembic remains single-head and upgrade tests cover fresh and supported existing databases.

**Rollback/recovery:** keep the old route dependency provider and response mapping until the new application query has passed contract tests. Revert route wiring independently of the new service. Do not drop tables or data. Defer any `create_all` bootstrap change until a restore-tested database plan and explicit supported-startup matrix exist; never depend on an untested Alembic downgrade.

### Phase 3 — Canonicalize capability and quality execution

1. Trace all entrypoints and outputs through `QualityService`, `DataOperationsService`, workflow engine, agents, capability executor and direct validation routes.
2. Select the existing execution path with widest tested behavior as canonical. Keep legacy facade calling that path until route, dashboard and plugin references are moved.
3. Replace `capabilities.cleaning -> services.data_operations` with an application-owned use case/port while preserving autofix/validation/report sequence.
4. Clarify validator plugin contract and move `validators/` implementations incrementally into/behind `plugins/`; preserve plugin-first discovery and legacy fallback until migrated categories and tests prove equivalent behavior.
5. Separate typed rule definitions/evaluation from rule retrieval/indexing without changing persisted rule pack formats or supported categories.

**Exit gate:** one application-facing quality/capability dispatch path, no duplicate active implementation, unchanged capability trace/result contracts, validator discovery/ordering and representative end-to-end tests.

**Rollback/recovery:** retain `DataOperationsService`, old validator modules and fallback registry until all consumers pass parity tests. Restore the prior facade/registry dispatch if any result, error, autofix order or trace changes unexpectedly. Do not rewrite stored datasets or reports as part of consolidation.

### Phase 4 — Canonicalize workflow runtime and planning

1. Trace authoring, simulation, synchronous execution, queued execution, worker, retries, state persistence, approval/risk gates and history reads.
2. Preserve `WorkflowRuntimeService` as application entry and `WorkflowEngine` as the execution engine unless evidence points to a different existing path. Queue implementations remain transport adapters.
3. Unify plan validation/context/trace boundaries only where duplicate behavior is demonstrated; retain capability version/dependency resolution semantics.
4. Make worker composition consume the same application ports and orchestration contract as API execution. Do not merge AI planning with deterministic authorization/execution decisions.

**Exit gate:** API and worker share one state-transition contract; sync/queued tests, retry/idempotency tests, approval/risk tests and execution trace persistence pass.

**Rollback/recovery:** keep the existing engine, queue backend and persisted state vocabulary operational until API and worker parity is shown. Revert the consumer switch and drain/replay using the existing idempotency contract if a queued-work rollout fails. Do not rewrite execution rows or discard traces.

### Phase 5 — Data model, compatibility, and physical structure

1. Classify each `models/`, `controllers/`, `views/`, root script, `ai/`, `schemas/`, `services/` and `repositories/` module by importers, runtime entrypoint and test coverage.
2. Keep `models.database` / `models.domain` and root launchers as explicit shims until a deprecation window and repository-wide/external consumer check are complete.
3. Resolve pandas/scikit-learn imports from domain by deciding which types/calculations are business contracts and which belong in quality adapters; pin numerical/output equivalence.
4. Move files only after import ownership and canonical destinations are settled. Do not target a `src/platform` tree for appearance alone.

**Exit gate:** no unclassified duplicate active implementation; shims have owner, target and removal condition; import and startup commands pass from documented entrypoints.

**Rollback/recovery:** physical moves are one file/package slice at a time with import shims retained. Revert the move and restore the compatibility import/entrypoint if repository imports, documented launches, tests or known external consumers break. Omit moves without demonstrated value. No broad tree rewrite and no database operation in this phase.

### Phase 6 — Documentation and final architecture audit

Update `docs/architecture/` and root audit after implementation, then generate `FINAL_ARCHITECTURE_AUDIT.md` with before/after graph, migrations, retained shims, violations fixed/retained, test and runtime evidence, Alembic status, security/observability limits and next work. The current discovery deliverables are not the final audit.

## Risk register and gates

| Risk | Why it is high | Required control |
|---|---|---|
| Workflow/execution consolidation | API and worker share persisted states, retries, traces, approvals, risk and changesets | Trace each state transition and failure path; preserve sync and Redis queue behavior with contract/integration tests. |
| Persistence consolidation | 23 migrations, multiple historical revision naming schemes, create_all at runtime | Never rewrite applied revisions or run destructive migrations; test upgrade from supported predecessor and fresh DB; explicit backup/rollback plan for production. |
| Authorization/compliance relocation | Cross-cutting workspace/tenant scoping and policy checks | Route-level tests for anonymous, owner, cross-workspace, roles, quota/compliance denials; compare before/after decisions. |
| Capability/quality path | Multiple direct and workflow-driven paths can yield different data or reports | Characterize current path per endpoint first; compare results, ordering and error semantics on fixtures. |
| Channel credential boundary | Encrypted credentials and outbound API calls | No credential exposure; test encryption/decryption, URL validation, retries and dry-run with fakes; never migrate secrets. |
| API schema relocation | 60+ documented OpenAPI operations in S27 claim | Snapshot OpenAPI paths, operation IDs, fields/status/error envelopes and execute route contract tests. |
| Compatibility removals | Legacy imports may be used outside repository | Deprecate first, retain shims, verify imports/entrypoints/docs and state explicit removal condition. |
| Startup side effects | Session factory creates all schema on construction | Move only after fixtures and deployment start-up paths are explicit; no production DB mutation in a structural PR. |

## Validation gates for every phase

- Import graph and `compileall`; static architecture direction checks.
- Targeted unit and API tests, then full regression. Test results must report pre-existing failures separately from regressions.
- Workflow, capability, persistence, security and property/fuzz tests relevant to changed modules.
- Build FastAPI app and create worker; verify dashboard launch where the slice affects it.
- Alembic heads and fresh/upgraded database validation for persistence edits; never apply migrations against an unapproved production database.
- Review dependency diff, duplicate owner inventory, public API diff, observability fields and compatibility shim conditions.
- Enforce the unchanged 193-module / 977-passing baseline at each behavior-changing slice and phase gate; state any deliberate collection change before merge.
- Record a phase-specific rollback/recovery action and its trigger before switching consumers. For persistence, recovery requires a backup restore rehearsal; a downgrade alone is not an approved rollback.

## Database safety boundary

Historical discovery snapshot (superseded): `services.container` called `database.models.make_session_factory()` for API and worker startup; the then-current factory called `Base.metadata.create_all(engine)`. Alembic used the same metadata with head `20260928_01`. Subsequent authorized work changed startup flags and the active migration graph; see the current implementation/evidence reports before relying on this snapshot.

## Proposed decision records

Before the corresponding migration, write ADRs for: application/persistence ports and repository ownership; authorization/governance service ownership; canonical quality/capability execution; canonical workflow engine/queue semantics; AI provider and copilot boundaries; ORM and migration/bootstrap boundary; public API/schema ownership; and compatibility-shim lifecycle. Each ADR should record context, evidence, decision, considered alternatives, consequences, tests and migration impact.

## Consumer and test crosswalk

These are existing test modules discovered in `tests/`, not newly added or rerun in this documentation pass. Run the relevant subsets and then the complete protected 977-test suite for each behavior-changing slice.

| Proposed order | Direct consumers / paths | Existing tests to anchor validation |
|---|---|---|
| First port experiment: agent memory | `application/memory/memory_service.py`, `repositories/agent_memory.py`, container wiring | `test_agent_memory_service.py`, `test_agent_memory_repository.py`, `test_agent_memory_integration.py` |
| Governance ports: authorization, compliance, quota | Approval, ChangeSet mutation, dataset, workflow, workspace application use cases; `services/authorization.py`, `services/compliance.py`, `services/quota.py` | `test_authorization_domain.py`, `test_authorization_service.py`, `test_authorization_persistence.py`, `test_compliance.py`, `test_compliance_service.py`, `test_compliance_repository.py`, `test_dataset_compliance.py`, `test_workflow_compliance.py`, `test_organization_quotas.py`, `test_approval_changeset_service.py`, `test_changeset_compliance.py` |
| Route queries and schema adapters | `api.dependencies`, `api/routes/{channels,executions,risk,data}.py`, API response mapping | `test_api_endpoints.py`, `test_api_channels.py`, `test_api_execution_detail_persistence.py`, `test_api_workflow_execution.py`, `test_api_studio.py`, `test_changeset_api.py`, `test_lineage_audit_api.py`, `test_api_marketplace.py`; compare generated OpenAPI. |
| Quality/capability path | `services.data_operations`, `services.validation_service`, `capabilities/*`, `execution/capabilities/*`, validator/plugin registry | `test_data_operations.py`, `test_quality_service.py`, `test_clean_extract_pipeline.py`, `test_capabilities.py`, `test_capability_execution_service.py`, `test_capability_executor.py`, `test_real_capability_chain.py`, `test_validation_capability_integration.py`, `test_plugins.py`, `test_rule_engine.py`. |
| Workflow/runtime and worker | `application/workflows/*`, `execution/workflow/engine.py`, queues, repositories and API/worker composition | `test_workflow_runtime.py`, `test_workflow_runtime_service.py`, `test_workflow_engine.py`, `test_workflow_engine_container.py`, `test_workflow_engine_full_persistence.py`, `test_workflow_execution_async_state.py`, `test_workflow_execution_worker.py`, `test_redis_workflow_execution_queue.py`, `test_api_workflow_execution.py`, `test_studio_workflow_real_capability.py`, `test_workflow_runtime_rbac.py`, `test_workflow_compliance.py`. |
| Persistence bootstrap decision (stand-alone, gated) | `make_session_factory`, container, Alembic env/revisions, unit-test DB bootstrap | `test_persistence.py`, `test_execution_trace_persistence.py`, `test_authorization_persistence.py`, `test_workflow_engine_execution_persistence.py`, `test_workflow_engine_failure_persistence.py`, `test_workflow_engine_full_persistence.py`, `test_workflow_execution_repository.py`; fresh and supported-upgrade DB checks are additional required gates. |
| Physical compatibility classification | `models/*`, `controllers/*`, `views/*`, `ai/*`, root entrypoints, schemas | Existing tests are not sufficient by name alone. Require reverse-import and documented launch checks plus the full regression suite before any move or shim removal. |

The route/service tests above pin API-visible behavior; repository tests pin persistence semantics; workflow/capability tests pin state transitions, traces and results. The crosswalk does not claim all behaviors are fully tested: gaps are unresolved questions below.

## Unresolved architectural questions (must be answered before relevant slice)

1. Which existing quality entrypoint is canonical per route: `QualityService`, `DataOperationsService`, direct capability calls, or workflow execution? Build an endpoint-to-call-graph and compare outputs/errors on fixtures before Phase 3.
2. Do `application/workflows/runtime_service.py` synchronous calls and `execution/workflow/engine.py` queued worker calls share every state transition, retry/idempotency rule, trace and approval gate? Trace both code paths before Phase 4.
3. Is `Base.metadata.create_all` intentionally supported only in local/test even though the current container invokes it for API and worker construction without an environment guard? Obtain supported deployment/startup evidence before changing schema bootstrap.
4. Which database starting states are supported (fresh, prior Alembic revisions, partially bootstrapped legacy)? Verify upgrade path and restore rehearsal before any persistence lifecycle change.
5. Which dashboard, controller, `ai/`, nested `models/*`, `views/*`, and root-script modules are runtime consumers or external compatibility surfaces? Enumerate imports, entrypoint references and docs.
6. Do pandas/scikit-learn operations under `domain/` express platform policy or dataframe implementation details? Review exact modules, public values and numeric parity tests before moving them.
7. Which schema package is contract source for each public route (`api/schemas.py` versus top-level `schemas/*`)? Snapshot OpenAPI and inspect actual imports before consolidation.
8. What is the complete `request.app.state.container` consumer set and do any dependencies rely on concrete container fields? A file import graph alone cannot answer this.
9. Which full-suite warnings and test-environment assumptions are part of the accepted baseline? Record warning identities in the first pre-migration baseline capture; do not silently normalize them away.

## PHASE 5 ENTRY CRITERIA

Phase 5 remains **NO-GO** until every criterion below is satisfied and recorded. Passing one criterion does not waive another.

- [ ] Phases 0–4 implementation slices (if authorized later) have actually been completed; their exit and rollback gates are recorded. A documentation-only plan is not evidence of code migration completion.
- [x] Discovery deliverables are present and cross-checked; repository code is clean at the tracked-file level. (This documents discovery only.)
- [x] Protected baseline evidence is recorded: 193 test modules, 977 passed; latest successful invocation and independent S28/handoff evidence are named.
- [ ] Immediately before Phase 5, rerun the entire suite in a repeatable environment: same test collection and 977 passed, with all warnings/failures accounted for. Repeat after every structural slice.
- [ ] Every Phase 5 file candidate has a named canonical owner, complete in-repo/runtime consumer list, explicit tests, external-consumer/deprecation decision, reversible action and rollback condition.
- [ ] Quality and workflow/capability canonical paths have behavior parity evidence across API, synchronous and worker consumers; authorization, approval, risk, changeset, lineage/audit, channel-sync and trace invariants are covered.
- [ ] Every proposed physical target path has been justified by measured ownership ambiguity or dependency benefit and proven by a preceding bounded slice. Unproven targets remain proposals; no blanket tree move is allowed.
- [ ] `create_all`/Alembic responsibilities and supported database starting states have an explicit, reviewed decision. Any database work has tested fresh/upgrade paths and a restore-tested recovery procedure; no destructive migration is bundled with file moves.
- [ ] All compatibility shims have an owner, destination, supported period and removal condition; no shim is removed while an importer or documented/external consumer remains.
- [ ] Phase 5 scope excludes `src/platform` unless separate repository evidence demonstrates a material benefit and a low-risk incremental route. Structural consistency alone is insufficient.
- [ ] `DISCOVERY_REVIEW.md` unresolved questions that affect the selected files are answered or explicitly accepted as residual risks; no security, data-loss, public-contract or ownership question is silently assumed.

**Decision rule:** any unchecked criterion means Phase 5 stays NO-GO. The current state has only the discovery/baseline criteria checked; Phases 1–4 code migrations have not been run, so Phase 5 is not eligible.

## Discovery completion boundary

This plan intentionally stops before source migration. Documentation for Phases 0–4 is finalized; their proposed code migrations remain unexecuted. The protected baseline is **977 passed**. `DISCOVERY_REVIEW.md` and the explicit Phase 5 criteria preserve the NO-GO until all gates pass.

## Pre-migration verification addendum (2026-09-29)

This addendum records repository evidence only. It changes no implementation, test, migration, runtime configuration, or database schema. It does not authorize Phase 5. Baseline evidence remains the prior recorded `977 passed`; this read-only investigation did not rerun tests.

### Quality and data-quality execution path

**Canonical ownership decision supported by current wiring:** `application.quality.QualityService` owns upload validation as an application use case; `execution.capabilities.CapabilityExecutionService` owns plan dispatch and capability lifecycle; registered implementations under `capabilities/` own reusable clean/validate/QA capability behavior; `domain.quality/` and `domain.validation/` own quality calculations and validation primitives. `application.quality.DataHealthService` owns the distinct persisted dataset-health/diagnostics use case. These are separate use cases; health metrics are not an alternate upload validator.

Observed upload path: `api/routes/data.py:/validate` and `/validations` → `QualityService.validate` → requirement interpretation (`data.qa`) and planning → `CapabilityExecutionService` → planned `data.clean` → `data.validate` → `data.qa` capabilities → validation result, persisted execution/trace/report and optional explanation. `ValidationCapability` delegates tabular checks to `services.validation_service.ValidationService`, which partitions DataFrame rows across category validator work; validators consume `domain.validation` primitives and/or rule retrieval. `QACapability` delegates score/anomaly work to QAAgent using `domain.quality.HealthScoreService` and `detect_anomalies`. The default container registers `CleaningCapability`, `ValidationCapability`, and `QACapability`. `/clean` and `/extract` use `DataOperationsService` directly; its cleaning behavior is also wrapped by `CleaningCapability`, so this is a transitional direct service boundary, not proof of two independent cleaning algorithms. `/mapping` uses `domain.catalog.MappingService`.

`plugins.registry.ValidatorRegistry` discovers plugins before built-in `validators/` implementations and uses first registration per category. `plugins.fashion.validator` is active; `validators.fashion` is an explicit re-export shim. `validators.cosmetics` and `validators.home_appliances` remain active fallback implementations using `domain.validation`; do not label the whole `validators/` tree dead. Runtime call sites also include the rule engine. Tests currently anchor use-case behavior (`test_quality_service.py`), a real API capability path (`test_api_endpoints.py::test_validate_uses_real_capability_pipeline`), capability unit/integration and real chain (`test_validation_capability.py`, `test_validation_capability_integration.py`, `test_real_capability_chain.py`, `test_cleaning_capability.py`, `test_capability_container.py`), legacy service/clean/extract (`test_data_operations.py`, `test_clean_extract_pipeline.py`), registry/rules (`test_plugins.py`, `test_rule_engine.py`), validation services (`test_validation_services.py`), QA agents (`test_ai_agents.py`), and the separate data-health tests (`test_data_health_domain.py`, `test_data_health_service.py`, `test_s15_data_health_api.py`). This coverage does not establish byte-for-byte or error/trace parity for every category, endpoint, workflow, or plugin precedence case.

**Migration proposal, paths remain unapproved:** preserve the use-case/executor/capability/domain owners above; introduce no parallel quality engine. First characterize `/validate`, `/clean`, `/extract`, workflow capability execution and registry fallback with shared category fixtures. If a narrow application-owned cleaning use case is evidenced, route both `/clean` and `CleaningCapability` through it while retaining `DataOperationsService` as a compatibility facade. Move a validator category only after plugin/fallback, rule, ordering, error, autofix and report parity tests exist. Candidate destinations are provisional and must be chosen per file; no broad `validators/` move is approved.

### Workflow synchronous/worker parity

`domain.studio.workflow.Workflow` is the workflow definition; `repositories.workflows` persists definitions and versions, including plan snapshots. `application.workflows.runtime_service.WorkflowRuntimeService` is the API use case; `execution.workflow.engine.WorkflowEngine` is the execution engine. API `/execute` and `/execute-async` both call the runtime service. With the production container's fully wired risk gate, synchronous execution persists/queues the execution record then calls `execute_existing` inline; asynchronous execution persists/queues and dispatches only its execution ID, then the worker claims it and calls the same `execute_existing`. Both normal paths load the pinned workflow version and use the same engine runtime/streaming implementation. Without the risk-gate collaborators, a compatibility fallback calls `engine.execute()` and resolves the active version; preserve that distinction until removed by evidence and tests.

The API use case performs owner/scope, authorization, compliance and quota checks before execution/dispatch and applies risk/approval policy. The worker does not repeat these request-time decisions: it claims `QUEUED → RUNNING`, delegates, and persists failure on a caught execution exception. The queue is transport only: in-process thread queue or Redis Streams carries execution IDs, while the database record is authoritative. Redis startup recovers idle pending messages with `XAUTOCLAIM`; successful return from the worker is followed by `XACK`.

Therefore business execution is shared in the normal production path, but lifecycle semantics are intentionally different: sync holds the request and returns the execution result; async returns a queued identifier/state and is subject to delivery, claim, acknowledgement and retry behavior. A material recovery gap remains: if a process dies after the DB claim changes state to `RUNNING` and before terminal persistence, replayed Redis delivery calls `claim_running`; a non-QUEUED record returns `None`, after which the consumer acknowledges the message. Repository code/tests inspected show no stale-RUNNING reconciler. Existing tests cover engine version snapshots, sync API/runtime, queue transport, worker claim and async state (`test_workflow_engine_version_snapshot.py`, `test_workflow_engine_versioning.py`, `test_api_workflow_execution.py`, `test_workflow_runtime_service.py`, `test_workflow_execution_worker.py`, `test_workflow_execution_async_state.py`, `test_workflow_execution_queue.py`, `test_redis_workflow_execution_queue.py`), but do not establish recovery after process death between claim and terminal write.

Required parity before any workflow migration: pinned version and stored inputs/plan; state transitions; single claim/concurrent duplicate behavior; sync return vs async queued response; authorization/compliance/quota/risk/approval; capability versions/order; streaming and whole-frame output; changesets, lineage, trace and audit; failure persistence; Redis pending recovery, acknowledgement and stale-RUNNING recovery. Do not silently change the identified crash window as part of structural consolidation; decide and test a recovery policy separately.

### Database schema lifecycle evidence and policy

`database.models.make_session_factory(url)` creates the engine and unconditionally calls `Base.metadata.create_all(engine)`. `services.container.Container` calls it for every container. `api.main.create_app` constructs that container; production Docker starts Uvicorn through `api.main:create_app --factory`. `worker.create_workflow_consumer` also builds the same container; the production worker starts `worker.py`. Thus `create_all()` is production-reachable in both API and worker startup; repository evidence does not establish whether a particular deployed database has exercised that path. `Settings.environment` has development/test/production values, but this call has no environment guard. Dashboard is an HTTP client and does not construct the container.

Historical discovery snapshot (superseded): Alembic used `database/migrations` and `Base.metadata`, with the former 23-revision chain at head `20260928_01`. The chain has since been archived and replaced by the active `20261002_01` baseline. The old reference to `20260923_01` was first corrected to `20260928_01` on 2026-09-29; the operator documents now identify `20261002_01`. Docker startup commands do not run Alembic. Historical tests constructed SQLite schemas with `Base.metadata.create_all()`; this does not verify PostgreSQL DDL.

`create_all()` adds absent metadata tables; it does not perform Alembic alterations or stamp `alembic_version`. On an Alembic-upgraded schema with matching metadata it can be a no-op, but the repository does not prove safe coexistence for all supported starting states. On an empty database it may create objects before historical Alembic revisions expect to create them. **Policy proposal:** Alembic revisions should be the sole authoritative application schema lifecycle for development and production, applied as a controlled deployment/release step. Retain `create_all()` in explicit isolated test fixtures and only in a deliberately documented local bootstrap if required. Do not remove or alter it in this verification. Before any later bootstrap change, define supported fresh/existing/partial states, test fresh upgrade and every supported predecessor, split explicit test setup from runtime container construction, rehearse backup restore, and verify API plus worker startup. No destructive migration, downgrade, data rewrite, or migration-history edit is proposed. The actual deployed startup database state remains unverified; policy conflict means the concern is not Phase 5 ready.

### Dashboard, AI, and compatibility consumers

Root `dashboard.py` is an active launcher shim: Compose/Docker and README use `streamlit run dashboard.py`; it delegates to `app.dashboard.main`. `app/dashboard.py` is the active Streamlit UI and calls `DashboardApiClient`, which uses HTTP endpoints for validation/history, project/workspace, health/diagnostics and Copilot. It does not import repositories or database services. `test_dashboard_client.py` tests mocked HTTP client behavior; no repository evidence found a Streamlit-render or deployed dashboard-to-API end-to-end test. Canonical owners: dashboard presentation/client under `app/`, API behavior in `api/` + application use cases. Keep root launcher until deployment/docs no longer consume it.

`ai/` and `controllers/` contain only empty package initializers in the inspected tree and have no in-repository import/runtime/test consumers. `views/` also has only empty initializers and no in-repository consumer. This resolves their in-repository use as unused scaffolding, not external compatibility: no evidence can exclude imports by outside scripts/deployments. Active AI implementation is under `agents/` and `application/copilot/`; `services.container` conditionally wires the optional Copilot model when configured and routes expose Copilot. Canonical AI use-case/tool policy owner is `application/copilot`; provider-facing agents remain adapters pending contract boundary evidence. `models/database.py` and `models/domain.py` re-export canonical `database.models` and `domain.models`; docs describe these as compatibility modules. `api/schemas.py` re-exports `schemas.responses` and docs call it backward-compatible. No in-repository consumers of these compatibility re-exports were found, but external importers are unknown. Root `main.py` delegates to `app.main` and is documented as a launch option; unlike empty scaffolding it has an explicit supported consumer. Do not delete or move any of these based only on absent internal imports.

### pandas and scikit-learn ownership

Pandas is imported across domain tabular models, validation/quality calculations, application use cases, infrastructure readers, capabilities, validators, agents, API serialization and the dashboard. The evidence supports ownership by the cross-layer tabular quality/validation subsystem for DataFrame semantics and quality/validation contracts; IO parsing stays infrastructure-owned, orchestration application-owned, and presentation remains in the dashboard. Pandas is not infrastructure-only. Any migration must preserve DataFrame input/output contracts, row ordering/indexes, null/type behavior and streaming/chunk semantics.

Scikit-learn appears in `domain/quality/anomalies.py` via `IsolationForest`; the QA runtime calls `detect_anomalies`, which affects quarantined rows and resulting score/report behavior. Its business-facing anomaly semantics belong to quality. Whether the estimator implementation should remain a domain-owned calculation or sit behind a quality adapter is not settled by imports/tests; retain current implementation and treat any physical dependency relocation as blocked until threshold/seed/output parity tests and optional-dependency policy are explicit.

### Final Phase 5 entry matrix

“Current owner” means the observed implementation/wiring location. “Canonical owner” records the evidence-backed responsibility; proposed physical paths are not approved. Every row currently says NO because the migration plan Phases 1–4 remain unexecuted, and a row-level owner decision does not authorize Phase 5.

| Concern | Current Owner | Canonical Owner | Evidence | Consumers | Tests | Migration Risk | Required Parity | Rollback | Phase 5 Ready? YES/NO |
|---|---|---|---|---|---|---|---|---|---|
| Services | `services/*`, including container and legacy use cases | Keep container as composition root for now; application use cases own business orchestration | Imports and runtime container wiring; several app→services edges remain | API routes, application use cases, capabilities, worker | service-specific suites; full protected 977 | High: hidden wiring/behavior consumers | same constructed graph, policies, errors and outputs | restore prior injection/constructor; retain facade | NO |
| Repositories | `repositories/*` | Repositories own persistence operations; application owns use-case policy | Repository call sites and ORM-backed adapters | services/container, API bypasses, app use cases | repository and persistence tests | High: query/scoping/transaction changes | query results, owner scope, ordering and transaction behavior | restore old repository adapter | NO |
| Persistence | `database.models`, `repositories/*`, `services.container` | Infrastructure/persistence owns engine/session and repositories; schema lifecycle policy below | make_session_factory and container call chain | API startup, worker startup, repositories, tests | persistence and repository suites | Critical: startup/data/schema state | same connection/transaction semantics; no data loss | app rollback plus restore-tested backup for any schema work | NO |
| Quality | `application.quality.QualityService`, `DataHealthService` | Quality upload use case: `application.quality`; persisted health: separate `application.quality.DataHealthService` | route and container wiring | data API, capability chain, dashboard HTTP, QA | quality/data-health/API tests | High: result/report/health distinctions | outputs, status/errors, persistence, reports, trace | restore route/container wiring and old facade | NO |
| Validation | `capabilities.ValidationCapability`, `services.validation_service`, `domain.validation`, `validators/*`, plugins | `domain.validation` contracts + capability orchestration; plugin/category implementations own category rules | registered capability, service and registry fallback | API quality, workflows, rule engine, category plugins | validation/rule/plugin/capability suites | High: category precedence and rule semantics | per-category rows/errors/order/autofix, registry precedence | retain legacy validator/fallback and restore registry | NO |
| Capabilities | `capabilities/*`, `execution.capabilities/*` | `capabilities` owns reusable operations; `execution.capabilities` owns dispatch/lifecycle | container registry and executor paths | QualityService, workflow engine/planner, API | capability executor/chain/container suites | High: dependency order/version/traces | plan order, versions, outputs, lineage and failure state | restore prior registry/dispatcher | NO |
| Execution | `execution/*` | `execution` owns deterministic execution engines and traces | service/container/engine wiring | application workflows, quality, workers | execution, trace, persistence suites | Critical: persisted transitions and idempotency | states, retries, duplicate claims, traces, failure persistence | revert consumer switch; preserve records; drain/replay only per validated contract | NO |
| Workflows | `domain.studio.workflow`, `application.workflows`, `execution.workflow` | Domain definition; application runtime use case; execution engine | API sync/async routes and engine version snapshot | API, worker, queue, dashboard status client | workflow engine/runtime/API/worker/queue suites | Critical: async crash gap and policy gates | pinned version, all gates, execution output and lifecycle; stale RUNNING policy | revert API/worker wiring; preserve queued/persisted records | NO |
| API boundaries | `api/routes/*`, `api/dependencies.py` | `api` owns HTTP mapping; application owns use cases; remaining bypasses require Phase 2 | route import/call-site census in discovery docs | clients, dashboard, integrations | API route tests and OpenAPI snapshot needed | High: public contract/auth bypass | paths, operation IDs, schemas, auth/scope/errors | restore route provider/response mapping | NO |
| Dashboard | root `dashboard.py`, `app/dashboard.py`, `app/api_client.py` | `app` owns dashboard UI and HTTP client; API owns server | Docker/Compose/README launcher plus HTTP imports | deployed Streamlit launcher, API endpoints | mocked client tests; no E2E UI proof | Medium: launch and route compatibility | launch command, HTTP paths, rendering and errors | restore launcher/client imports | NO |
| AI/agents | `agents/*`, `application/copilot/*`; empty `ai/*` scaffold | `application/copilot` owns use case/tool policy; provider/agent adapters retain provider boundary; `ai/` external use unknown | container conditional wiring and Copilot route; empty tree scan | Copilot API, quality agents/planner, optional model provider | agent/Copilot tests with fakes; provider-connected runtime not covered | High: optional provider, outputs, external imports | tool allowlist/authorization/events/streaming and no-key path | retain old imports/provider wiring; no deletion without deprecation evidence | NO |
| Database schema lifecycle | runtime `create_all()` plus Alembic revisions | Alembic as proposed authoritative app schema mechanism; explicit test fixtures own test bootstrap | prod-reachable API/worker call; README/runbook; head `20260928_01`; stale runbook text corrected | API, worker, local setup, tests, deploy operator | isolated schema tests; fresh/existing upgrade and restore checks absent | Critical: fresh/partial DB conflict/data loss | schema equivalence, single head, API/worker startup, restore | no destructive operation; revert code only after validated DB recovery/backup | NO |
| pandas / scikit-learn | pandas cross-layer; sklearn in `domain.quality.anomalies` | Quality/validation subsystem owns tabular semantics and anomaly policy; sklearn implementation placement unresolved | import scan plus QAAgent call site | application, capability, API, dashboard, QA | validation/quality tests; explicit numeric parity gaps | High: dtypes, ordering, anomaly rows/score | DataFrame and exact anomaly/quarantine/score outputs | keep current imports/implementation and facade | NO |
| Compatibility modules | root launchers, `models/*`, `api/schemas.py`; empty `controllers/`, `views/`, `ai/` | canonical targets per re-export documented above; external use unresolved for shims | launcher/docs and re-export bodies; no internal consumers of several shims | deployment/docs/internal imports; external unknown | client/schema/entrypoint coverage incomplete | Medium/high: out-of-repo imports | imports and documented launches stay valid throughout deprecation | keep old path as re-export/launcher; revert move | NO |

No matrix entry approves a source edit. Before Phase 5, replace every NO only with evidence from completed Phases 1–4, parity and rollback gates—not by editing the proposed owner name.

### Updated unresolved questions and Phase 5 gate

Resolved/bounded by this repository pass: canonical quality use cases and capability chain; workflow definition/use case/engine/queue responsibilities; in-repository dashboard launcher/UI/client and active AI owner; empty in-repository scaffolding status; pandas cross-layer ownership; sklearn quality responsibility. Still blocked: full quality parity across all consumers/categories; worker crash-after-claim recovery and stale-RUNNING policy; actual production database starting state and safe coexistence of runtime create_all with Alembic; external consumers of compatibility paths; exact sklearn implementation boundary; Streamlit end-to-end and production provider runtime evidence. See `DISCOVERY_REVIEW.md` → **PHASE 5 ENTRY REVIEW** for the itemized disposition.

**PHASE 5 ENTRY CRITERIA (reaffirmed):** Phase 5 remains NO-GO until (1) Phases 0–4 are completed and their gates/evidence recorded, (2) the exact 193-module/977-pass suite is rerun immediately before and after each structural slice with warnings accounted for, (3) every selected file has canonical owner, complete consumers, tests, external-compatibility decision, reversible action and rollback, (4) quality and sync/worker business and failure/recovery parity are demonstrated, including a tested stale-RUNNING/Redis recovery policy, (5) database startup states and Alembic authority are reviewed and fresh/upgrade/API/worker/restore gates pass before any bootstrap change, (6) each target path is proven by a bounded preceding slice and no `src/platform` tree is presumed, (7) dashboard/AI/provider/compat consumers are either verified or protected by retained shims, (8) pandas/sklearn contracts and numeric outputs are pinned, and (9) no unresolved security, public contract, data loss or ownership blocker is silently accepted. No destructive DB migration is part of early phases or file moves.

### BLOCKER RESOLUTION ROUND 2 — FINAL EVIDENCE MATRIX (2026-09-29)

This section supersedes earlier “focused tests not run” wording above. It records a focused selection of **114 passed in 10.02s**; the accepted full baseline is **193 modules / 977 passed in 64.81s** from the earlier canonical run and was not rerun in this round. Exact focused command is preserved in `BLOCKER_RESOLUTION_REPORT.md`. No code, test, schema, migration or runtime configuration changes were made. All physical targets below remain proposals; this matrix does not authorize Phase 5.

| Concern | Current Owner | Canonical Owner | Evidence | Consumers | Tests | Migration Risk | Required Parity | Rollback | Phase 5 Ready? |
|---|---|---|---|---|---|---|---|---|---|
| Services | `services/` concrete adapters plus application use cases | Application owns orchestration; infrastructure/repository boundary owns adapters | Container and call-site wiring; earlier dependency inventory | API, capabilities, workflow engine, worker, agents | Focused quality/workflow tests 114 pass; no broad boundary proof | High: hidden direct callers and lifecycle wiring | Behavior, exceptions, transactions and startup identity | Restore prior import/service path; rerun baseline | NO — existing couplings remain; no slice validated |
| Repositories | `repositories/` | Repository interfaces/implementations remain at evidenced current boundary; per-concept owner | Runtime call sites and persisted models | Quality, workflow, dashboard-facing APIs, DataHealth | Focused persistence/workflow tests pass; upgrade-state coverage absent | High: persistence contract and schema coupling | Query, transaction, serialization and record semantics | Revert consumer imports; preserve schema/data; restore backup for schema effects | NO — DB lifecycle unresolved |
| Persistence | `database/`, `repositories/`, direct `create_all` wiring | Infrastructure persistence boundary; specific target path unproven | `make_session_factory`, container/API/worker wiring; Alembic config | API startup, worker startup, services/repositories, tests | Focused persistence tests; no migration upgrade tests | Critical: production startup/schema safety | Session, transaction, metadata and migration behavior | Tested backup/restore plus revert code; restore state if schema changed | NO — production-reachable create_all and fresh DB failures |
| Quality | `application.quality.QualityService` | Application quality use case; keep `DataHealthService` distinct | `/validate` route and capability plan chain | API, capabilities, AI/agents, reports, DataHealth | API/quality suite; real cap chain; 114 focused pass | High: errors, cache, reports, partial traces | Status/errors, outputs, reports, issue ordering, traces, persistence | Keep facade/import path; roll back consumer routing; baseline | NO — cross-path parity partial |
| Validation | `capabilities/validation.py`, `services/validation_service.py`, `plugins/`, `validators/`, `domain/validation/` | Capability orchestration + domain validation primitives; plugin/fallback per category retained | Registry discovery precedence, category validators and rule retrieval | Quality API, workflow capabilities, plugin consumers | Validation, plugin, rule, integration tests passed | High: plugin-first precedence, category/autofix/order | Per-category rules/issues/autofix/order/error semantics | Restore registry/fallback route and package import shims | NO — category-wide parity incomplete |
| Capabilities | `execution/capabilities/` executor and `capabilities/` implementations | Executor owns dispatch; capability implementations own each operation | Container registration, real chain tests | QualityService, WorkflowEngine, worker through engine | Capability + real chain tests; 114 focused pass | High: plan/API/workflow output differences | Dispatch, trace and failure behavior | Revert dispatch/import changes; preserve old registrations | NO — full workflow and worker quality parity absent |
| Execution | `execution/workflow/engine.py`, repositories and worker | `WorkflowEngine` owns execution; persistence owns durable state; worker is transport consumer | Production container, runtime and worker wiring | Sync/async APIs, Redis/in-process queues, dashboards | Engine/runtime/worker/queue tests | Critical: duplicate/lost executions and partial outputs | State transitions, IDs, idempotency, errors, traces, recovery | Replay only under defined idempotency policy; restore durable state from verified backup | NO — crash recovery unresolved |
| Workflows | Domain workflow + repository version snapshots; runtime use case | Domain definition, `WorkflowRuntimeService`, `WorkflowEngine` are distinct evidenced owners | Pinned version plan path through API and engine | API, persistence, sync caller, worker | Snapshot, runtime, API, real clean+validate studio tests | High: version/fallback and plan serialization | Pinned plan, validation, authorization timing, step results | Preserve old version lookup/serialization and API routes | NO — policy/recovery parity open |
| API boundaries | `api/routes/*`, `api/main.py` with some direct service/repository access | API owns transport/auth/error mapping; application use cases own work | API route and container call sites | HTTP clients, dashboard, external clients | API focused tests passed | High: public status/error/schema/alias contracts | Paths, auth, status, response, errors and compatibility | Retain route aliases and response adapters; revert handler wiring | NO — selected public-contract parity not completed |
| Dashboard | Root `dashboard.py`, `app/dashboard.py`, `app/api_client.py` | `app.dashboard` UI/client with root launcher retained | Compose/README entrypoints; mocked client tests | Operators and documented launcher users | Dashboard client only; no deployed E2E | Medium/high: launch path and API expectations | Launcher, API contract, auth/session and rendering | Restore root script/client routes; keep compatibility launcher | NO — UI end-to-end unverified |
| AI/agents | `agents/`, `application/copilot/`; empty `ai/` scaffold | Active agents + application Copilot; compatibility scaffold target unproven | Container/API/provider wiring; docs | API/Copilot, optional Google provider | `test_ai_agents.py`; live provider not tested | High: provider/import/config assumptions | Tool outputs, provider errors, optional-key behavior | Retain shims/provider settings and revert import paths | NO — external provider and shim use unknown |
| Database schema lifecycle | `make_session_factory.create_all` plus Alembic | Policy owner unresolved; migration docs propose Alembic authority but repo evidence does not establish it safely | Fresh SQLite Alembic failed `NoSuchTableError(datasets)`; create_all→Alembic failed SQLite circular dependency; head `20260928_01`; no upgrade tests | API and worker startup, deploy operators, tests | No Alembic bootstrap/upgrade/restore test found | Critical: fresh install, deployed DB loss/startup outage | Fresh and predecessor upgrade, partial state, startup, schema equivalence, restore | Verified backup/restore, tested supported rollback/forward recovery | NO — blocking |
| Dashboard/AI/compatibility shims | Root launchers, `models/*`, `api/schemas.py`, `ai/controllers/views` | Keep evidenced active launchers/public re-exports; external owner unresolved | README/docs/Compose and repo-wide internal references | Internal imports, external unknown | Unit/client tests only; external consumer inventory impossible from repo | High for public or external import breakage | Import paths, CLI launch and documented integration contracts | Keep shim and revert routing; no deletion | NO — external consumers unbounded |
| pandas / scikit-learn | pandas across tabular contract; sklearn lazy import in `domain.quality.anomalies` | Quality subsystem owns anomaly semantics; exact implementation boundary unresolved | Single IsolationForest import and QAAgent caller; index/quarantine behavior traced | QA capability, direct quality and workflow serialization | Focused QA test; no dedicated anomaly output/version test | High: dtype/index/numerical drift and quarantine changes | Exact indices, score, quarantine, report and supported-version outputs | Keep implementation/dependency in place; revert adapter and compare fixtures | NO — numerical parity unresolved |

#### Explicit decisions and unresolved questions

- Confirmed: direct quality path uses `QualityService → CapabilityExecutionService → planned capabilities`; `DataHealthService` is a separate read-only use case. Registry precedence is plugin-first; Fashion plugin and Cosmetics/HomeAppliances fallbacks are active. No `src/platform` move is justified.
- Confirmed: normal production sync and worker workflow execution use the same pinned plan and engine method. Response timing, queue delivery, reports and persistence differ; API-time authorization/compliance/quota/risk checks are not repeated by the worker.
- Unresolved: whether delayed work must revalidate those gates; whether direct API/workflow quality should share report/log persistence; whether DataHealth must consume upload/workflow outcomes; behavior contracts for cache hit and partial failure trace.
- Unresolved runtime blocker: crash after DB claim can strand RUNNING state; Redis message recovery does not recover DB claim, and ACK follows a normal no-op worker return. Define and test recovery/idempotency before worker changes.
- Unresolved database blocker: `create_all` is reachable from API and worker startup; both tested fresh SQLite orderings failed; existing deployed states, supported DB engine behavior, Alembic authority, API/worker startup safety and restore have not been established.
- Unresolved compatibility: repository evidence cannot prove external imports absent. Keep public/documented launchers, schemas and shims; no removal/deprecation target is approved.
- Unresolved sklearn contract: implementation purpose/consumer is known, but exact anomaly-set/version/quarantine/report parity is not tested.

#### Exact Phase 5 entry criteria

Phase 5 remains **NO-GO** until every condition is evidenced and reviewed:

1. Preserve/reconfirm the unchanged canonical baseline (**193 modules / 977 passed**) in an approved writable test environment immediately before a later first slice, with all warnings/errors accounted for.
2. Define and test quality contracts for API, capability, workflow and worker execution, including all active categories/plugin precedence, errors, issue ordering, autofix, cache, partial traces, reports, persistence, and DataHealth linkage decision.
3. Define and test sync/worker semantics for pinned plans, policy-gate timing, retries, duplicate delivery, terminal failures, traces, reports and delivery. Crash after claim must have an approved idempotent recovery policy plus a passing failure-window test.
4. Decide DB schema authority and supported fresh/existing/partial states. Pass fresh bootstrap, predecessor upgrade, create_all/Alembic coexistence policy, schema equivalence, API/worker startup, and backup/restore/recovery tests for every supported DB engine.
5. Establish compatibility/provider/external consumer decisions for each selected path; preserve old public surfaces until deprecation is evidenced and consumers have a transition.
6. Pin pandas/scikit-learn inputs and outputs, supported-version anomaly sets, quarantine, score and report semantics before moving quality code or dependencies.
7. For each proposed file slice, record verified current consumers, exactly one canonical owner, evidence-based target path, tests, risk, rollback/recovery and baseline result. Keep targets proposals until proven; do not introduce `src/platform` for symmetry.
8. Complete the authorized Phase 0–4 documentation/evidence gates; do not treat those documents as source migration completion. No destructive DB migration belongs in early phases.

#### Recommended first migration slice

No first slice is ready now. After all entry criteria pass, use the smallest isolated, non-schema slice whose consumers and rollback are demonstrably bounded. The previous candidate (`application/memory/memory_service.py` behind `repositories.agent_memory`) remains a proposal only; revalidate its current consumers, exact target and tests at that time. This report does not authorize it or any Phase 5 work.

### Initial blocker-resolution refresh stop (historical; superseded below) — 2026-09-29

The required canonical baseline command was run before any focused parity tests:

- Command: `.\venv\Scripts\python.exe -m pytest -q` (PowerShell).
- Environment: Python 3.13.15 (64-bit), Windows 11 build 26200, pytest 9.1.1; executable `D:\Autonomous_E-commerce_Data_Operations_Platform\venv\Scripts\python.exe`.
- Result: **874 passed, 0 failed, 103 errors, 0 skipped, 2 warnings; 99.80 seconds**. The 977 outcomes sum to the previously recorded 977 test cases; this run did not repeat a separate module-count report.
- Comparison: prior protected baseline is 977 passed (193 modules), so this run is not a passing baseline and cannot replace it.
- Classification: **environment-related, high confidence**. Representative setup errors show `PermissionError: [WinError 5] Access is denied` while pytest's `tmp_path` fixture accesses `C:\Users\Admin\AppData\Local\Temp\pytest-of-JamesDR`. Tests reached by fixtures not needing that inaccessible temp location passed; no production-code failure is established by this run. Because the user explicitly required STOP on a differing baseline, no elevated rerun, focused quality/worker tests, or code change was made.

At the time of this initial stop, test-dependent investigations (quality parity and worker crash recovery) were **BLOCKED** pending a repeatable 977-pass environment. The later section below records that the baseline was reconfirmed outside the sandbox; those focused investigations remain unrun because this task stops after baseline verification. Repository topology findings remain as previously documented. Compatibility external-use claims remain unknown by repository-only evidence; database deployment starting-state safety remains unproven; scikit-learn numerical parity remains untested. See `BLOCKER_RESOLUTION_REPORT.md` and `DISCOVERY_REVIEW.md` for current statuses. Phase 5 remains NO-GO.

### Test-environment recovery and baseline reconfirmation — 2026-09-29

The baseline mismatch was isolated to sandbox filesystem access. `pytest.ini` has no `basetemp` setting; `TEMP` and `TMP` resolve to `C:\Users\Admin\AppData\Local\Temp`, and Python's `tempfile.gettempdir()` resolves there when the directory exists. The minimal existing test `.\venv\Scripts\python.exe -m pytest -q tests/test_api_marketplace.py::test_install_signed_rule_pack_endpoint` reproduced `PermissionError: [WinError 5] Access is denied` in sandbox `tmp_path` setup. In-sandbox use of a newly created repo-local temp directory also failed because the sandbox denied pytest's child-directory creation. Outside the sandbox, the same test passed (1 passed in 1.78s).

Read-only Windows ACL evidence showed the Windows Temp root and the failing `pytest-of-JamesDR` directory are owned by `JAMESDR\JamesDR`; the root grants that identity FullControl and the child has OWNER RIGHTS FullControl. Existing `.pytest_cache`, `.pytest-tmp`, and `codex-pytest-temp` are similarly owner-controlled. No ACL or repository pytest configuration was changed. The failure is the sandbox process boundary, not an underlying owner ACL defect. No external Windows ACL change is required. A sandboxed test process needs explicit writable access to its temp and cache paths; otherwise run tests in an approved current-user process context with that access.

The exact canonical command was then run outside the sandbox with the existing environment and no pytest options: `.\venv\Scripts\python.exe -m pytest -q`. Result: **977 passed, 0 failed, 0 errors, 0 skipped, 0 warnings reported, 64.81 seconds**. Protected baseline **193 modules / 977 passed: RECONFIRMED**. Historical baseline warnings are not rewritten; the latest run printed no warning summary. This reconfirms test baseline only. Phase 5 remains NO-GO, and this recovery task stopped before quality/worker parity tests as instructed.

### PHASE 4.5 — RUNTIME CORRECTNESS REMEDIATION STATUS (2026-09-29)

This is the latest Phase 4.5 gate and supersedes the round-two statuses where behavior changed. No Phase 5 migration, package move, or dependency change occurred. Regression assertions were folded into existing test modules; collection remains 193 modules / 977 tests.

| Blocker | Before evidence | Narrow change | Regression test | After evidence | Remaining risk | Phase 5 consequence |
|---|---|---|---|---|---|---|
| Execution crash after claim | `QUEUED→RUNNING`, worker dies, `XAUTOCLAIM` redelivers, queued-only claim returns `None`, normal worker return lets consumer ACK while row remains RUNNING. Terminal writes were not compare-and-set. | Redis consumer renews its own pending delivery while handling it. Reclaimed delivery uses existing worker/repository abstractions to conditionally mark a still-RUNNING execution FAILED, persist error/finished time and state transition, then ACK. No automatic retry because side effects are not generally idempotent. Completion/failure are conditional and cannot overwrite terminal state. | Expanded existing `test_workflow_execution_async_state.py`, `test_redis_workflow_execution_queue.py`, `test_worker_entrypoint.py`. Crash window simulated from durable claim to recovered message; duplicate recovery/late completion rejected; Redis lease renewal and callback wiring asserted. | Targeted regressions, focused suite and full canonical suite pass. | Redis lease expiry during process/network pause can make active work FAILED; prior side effects cannot be rolled back; no automatic retry. | Crash-stuck state resolved for covered Redis delivery. Accept lease/retry policy operationally before worker changes. |
| Fresh test/development schema | `make_session_factory` created 31 metadata tables; behavior was not explicitly specified. | Retain metadata bootstrap for development/test; regression verifies tables and first repository query. | Existing `test_persistence.py`. | Pass. | `create_all` is not an Alembic upgrade. | Ready only for fresh test/development initialization. |
| Alembic-managed/production startup | API and worker `Container` always ran `create_all`, mixing runtime setup with migration ownership. | Production Container disables `create_all` and requires current Alembic head before constructing repositories. API and worker share Container behavior. Alembic history unchanged. | Existing `test_persistence.py` prepares current-head schema, checks no schema mutation, and constructs API/worker with production policy. | Pass against test-stamped current-head SQLite schema. | Actual production Postgres schema, operator order and schema equivalence are not proven. | Partial. |
| Fresh Alembic / existing upgrades | Empty SQLite → `NoSuchTableError: datasets` at d14; `create_all`→Alembic → SQLite `CircularDependencyError` at 7757. No base revision. | Did not rewrite historical revisions. Added a bounded upgrade regression from `20260926_01` to `20260928_01` to prove the latest data backfill on an existing-shaped database. | Existing `test_persistence.py`, data-bearing Alembic upgrade. | Latest upgrade edge passes; exact clean-install failures remain known and no fresh Alembic success is claimed. | Earlier revision edges, legacy schemas, production database engines and restore remain uncovered. | UNRESOLVED critical DB gate. Establish safe production bootstrap and supported-state/restore evidence before Phase 5. |
| Representative quality workflow parity | Real worker quality path untested; sync test used engine inline; worker unit test used fakes. | No production behavior change; test actual streaming `data.clean→data.validate` through inline engine and worker with the same DataFrame chunk source. | Existing `test_studio_workflow_executes_real_capability_chain` extended to compare inputs/outputs, dispatch, rule-backed traces, state, persistence and validation-error behavior. | Matching traces and outputs; both complete, and the same invalid category fails identically. | Only this streaming workflow is covered. Direct API report/cache and all-category parity remain unproven. Workflow's lack of direct QualityService reports is an existing use-case distinction. | Partial; do not claim system-wide quality parity. |
| Protected baseline | Accepted 193 modules / 977 passed. | Regression coverage kept in existing test modules; canonical command unchanged. | Full and focused suites. | Focused **124 passed in 14.05s**. Canonical `.\venv\Scripts\python.exe -m pytest -q`: **977 passed in 66.12s**; collection **193 modules / 977 tests**. | Windows pytest temp/cache access still requires an approved writable context. | Baseline reconfirmed. |

#### Revised Phase 5 entry criteria

Phase 5 remains **NO-GO** until all earlier criteria plus the following are proven:

1. Define/test Redis lease expiry, process pause, duplicate deliveries and operator resubmission semantics. Confirm the no-auto-replay policy is acceptable for side-effecting capabilities and document Redis pending-message durability assumptions.
2. Provide supported fresh production provisioning. Current test/dev `create_all` success is not evidence that empty-database `alembic upgrade head` works; it currently fails. Do not promote the current-head stamp test as proof of fresh migration.
3. Test every supported existing schema predecessor and production DB engine, including API/worker startup against operator-migrated data, schema equivalence and backup/restore. Only the `20260926_01→20260928_01` SQLite edge is verified.
4. Complete quality parity for direct upload/API, all active categories, workflow and worker use cases if in migration scope; the one streaming workflow test is bounded evidence only.
5. Keep the 193-module / 977-pass baseline and all existing public imports/launchers intact; preserve rollback/recovery evidence per exact proposed slice.
6. Retain target paths as proposals; no `src/platform` move or Phase 5 work is authorized by this remediation.

**Recommended first Phase 5 slice: none yet.** Reassess only after clean production DB bootstrap and supported existing-state/restore blockers are resolved. The memory-service candidate remains a proposal and is not authorized.
## PHASE 4.6 UPDATE — 2026-09-29

Phase 5 remains **NO-GO**. No source, test, migration, schema, dependency, or runtime configuration changed in this verification.

### Entry matrix delta

| Concern | Current owner | Canonical owner | Evidence | Consumers | Tests | Migration risk | Required parity | Rollback | Phase 5 ready? |
|---|---|---|---|---|---|---|---|---|---|
| Persistence bootstrap / Alembic | Alembic revisions assume some pre-existing tables; application startup uses production `create_schema=False` and requires head | Alembic for production schema; clean-install prerequisite remains undefined | Empty SQLite `alembic upgrade head` fails at `d14c1f2a9b31` inspecting missing `datasets`; `0001_persistence` does not create it; later revisions assume datasets/workflow_executions | API and worker startup require migrated head | Existing 20260926→20260928 upgrade passes; exact clean bootstrap fails | High: no reliable empty production provisioning path; PostgreSQL not tested | Empty DB → supported baseline → head → app startup/use on supported production engine | Do not revise history or stamp/create schema until authoritative baseline and deployment start state are established; preserve current DB and backup before any later migration | **NO** |
| Direct API quality reports | `application.quality.QualityService` | Application quality use case owns generation/orchestration; ReportAgent renders; repository persists associations | Real API test; direct route returns execution-scoped format URLs. Workflow contract returns outputs/traces, no report API promise | `/validate`, `/validations`, report retrieval endpoint | `test_api_endpoints.py::test_validate_uses_real_capability_pipeline`; report generator/repository tests | Medium: report URL and persistence semantics are public API behavior | Preserve report formats and execution-specific associations in any later API slice | Revert application/API slice and restore report directory/artifact plus DB backup if persistence changes | **YES, boundary classified** |
| Quality cache | Application-owned `Cache` protocol; infrastructure `TTLCache` | Application use case owns policy; infrastructure owns TTL storage | Key = source bytes + resolved category + rule version hash; monotonic TTL; no explicit invalidation; lookup after execution/trace/context/status, before result/report save | Direct API QualityService only; worker workflows do not consume it | QualityService/API tests cover uncached response; no complete hit-side-effect contract test | Medium: current hit skips per-attempt result save after creating/completing a distinct execution row | No worker parity requirement established; decide whether each cached request needs a complete persisted attempt before touching cache behavior | Revert isolated application/cache slice and clear only cache state; preserve execution/report rows | **NO for a cache-specific slice** until hit persistence semantics are decided; **not a current cross-runtime architecture blocker** |
| Validator categories | `plugins.ValidatorRegistry` selects implementations; `capabilities.ValidationCapability` provides common dispatch | Validator/plugin subsystem owns category implementation behind common capability contract | Categories Cosmetics/Fashion/HomeAppliances; plugin-first discovery; Fashion plugin plus legacy import alias; other category-specific validators | API and workflow/worker via shared validation capability | Registry/category tests, validator-specific tests, Fashion sync/worker real streaming test | Medium: dispatch, autofix, rule source, issue shape and order may be category-specific | Maintain capability input/output/error contract; do not require identical rules/results; worker E2E for Cosmetics/HomeAppliances remains untested | Revert only the selected validator adapter change; retain plugin and legacy import surfaces | **YES for ownership classification; NO for a slice that changes untested categories** |
| Worker recovery and representative quality | `WorkflowExecutionWorker` / existing execution repository and Redis queue | Existing worker/execution boundary | Phase 4.5 atomic terminal writes, redelivery recovery and representative Fashion clean→validate inline/worker evidence | Async workflow API, worker process, Redis queue | Existing focused worker and real capability regressions | Side effects may precede failure; Redis lease/ACK semantics remain operational risk | Preserve same pinned workflow version, capability dispatch, issues/results/traces and terminal state for the proven sample | Existing idempotent conditional failure/terminal-state semantics; no automatic retry | **YES within tested scope** |

### Phase 5 entry criteria — updated

1. **Clean database bootstrap is a hard blocker.** Establish the authoritative pre-Alembic schema or a safe new clean-install path without bypassing Alembic or restoring production `create_all`; prove empty supported production DB → Alembic head → application and worker startup → first repository operation. Test on the supported production engine. The current SQLite failure at `d14c1f2a9b31` means this criterion is not met.
2. Validate the supported prior-version upgrade edges and application startup against real Alembic-managed schema; document backup, restore, and rollback assumptions. The one SQLite `20260926_01 → 20260928_01` test is bounded evidence only.
3. Retain worker crash recovery and representative sync/worker semantics already proven; decide Redis lease expiry and side-effect retry policy before any worker slice.
4. Preserve the direct API report contract. API report generation is an application use-case concern; workflow execution has no current report-path contract. No artificial parity requirement is imposed.
5. Cache remains API/application-owned, TTL storage remains infrastructure-owned. Before a cache-specific change, decide whether every cache-hit request must persist a complete execution result; current call ordering creates/completes the new row before returning a previous summary. Worker cache parity is not an existing requirement.
6. Keep the shared validator capability contract. Cosmetics and HomeAppliances are category-specific and not yet proven end-to-end through the worker; do not include those behaviors in a migration slice until targeted worker coverage exists.
7. Keep all physical target paths proposals until consumer evidence supports them. Preserve compatibility import paths. Do not add `src/platform`.
8. Reconfirm unchanged **193 modules / 977 passed** canonical baseline immediately before any later authorized first slice.

**Recommended first Phase 5 slice: none.** Resolve the clean database lifecycle blocker and make the required cache product/persistence decision first.

## MIGRATION HISTORY STATUS — PHASE 4.7 (2026-09-29)

- **FORMER_MIGRATION_HISTORY_STATUS:** the archived graph was a connected chain of 23 revisions at head `20260928_01`; first reference to `datasets` was `d14c1f2a9b31`; empty PostgreSQL bootstrap was unsupported. `7757af5afe0a` and `fcbc1a52044c` both created `workspaces`. Current active graph status is recorded in `MIGRATION_REPAIR_IMPLEMENTATION.md`.
- **AUTHORITATIVE_SCHEMA_SOURCE:** Git evidence shows historical application startup called `Base.metadata.create_all()` before additive revisions were introduced. This is the only repository-supported explanation for omitted base tables, but it is not a verified historical production DDL contract. No standalone baseline SQL/migration/init artifact exists.
- **PRODUCTION_SCHEMA_STATUS:** **PRODUCTION SCHEMA STATE = UNVERIFIED.** Compose/docs specify PostgreSQL 16 but no production database or schema evidence is available.
- **MIGRATION_REPAIR_REQUIRED:** required to provide a safe supported bootstrap for today's Alembic-first production startup; exact repair mechanism undecided because baseline is unknown. No migration history was changed.
- **MIGRATION_REPAIR_CONFIDENCE:** high that empty bootstrap is incomplete; medium-high historical model was a pre-provisioned baseline; low confidence in any particular repair until production state and authoritative baseline are evidenced.

The full 23-revision chronological inventory and Git/source analysis are in `BLOCKER_RESOLUTION_REPORT.md` under **PHASE 4.7 — MIGRATION HISTORY FORENSICS**. Phase 5 remains **NO-GO** pending a versioned/verified bootstrap contract and production-schema evidence. No code or database change is authorized by this forensic report.

## PHASE 4.8 — PRODUCTION DATABASE CONTRACT

- **PRODUCTION_DB_ENGINE:** PostgreSQL.
- **PRODUCTION_DB_VERSION:** 16 in production Compose/docs; deployed runtime version unverified.
- **PRODUCTION_SCHEMA_PROVISIONING_METHOD:** unknown for production. Historical API/container startup ran ORM `Base.metadata.create_all()`, but actual production use is unproven; current production path disables it. No SQL/init/bootstrap artifact is checked in.
- **PRODUCTION_MIGRATION_METHOD:** operator runbook says `alembic upgrade head`; Compose has no migration service, command, or entrypoint. The migration runbook and deployment guide are incomplete as a single executable order.
- **PRODUCTION_STARTUP_ORDER:** PostgreSQL/Redis health → API, worker and dashboard; Nginx waits for API health and dashboard. No schema stage runs in Compose; application requires current Alembic head.
- **PRODUCTION_SCHEMA_BASELINE:** INSUFFICIENT; tracked SQLite DB is not a PostgreSQL baseline.
- **PRODUCTION_SCHEMA_BASELINE_CONFIDENCE:** LOW for production schema claims.
- **POSTGRESQL_RUNTIME_VERIFICATION:** UNAVAILABLE (`docker`, `psql`, and `pg_isready` unavailable; no authorized isolated instance identified).
- **ALEMBIC_TAKEOVER_STATUS:** NO for empty PostgreSQL; UNKNOWN for existing production state and general future upgrades.
- **MIGRATION_REPAIR_STATUS:** BLOCKED; baseline/provisioning must be established first.
- **PHASE_5_GATE:** NO-GO.

Historical `create_all()` is evidence of a plausible app-driven baseline source, not evidence of production use. No external/manual provisioning path is documented. See the Phase 4.8 evidence and feasibility matrix in `BLOCKER_RESOLUTION_REPORT.md`. Do not begin repair until authoritative PostgreSQL baseline/provisioning evidence exists.

## PHASE 4.9 — EXTERNAL EVIDENCE GATE

Repository-side investigation is closed. Before migration repair, obtain one authoritative production-equivalent artifact: isolated PostgreSQL 16 staging database, schema-only PostgreSQL dump, approved schema snapshot, authoritative provisioning artifact, or equivalent deployment database artifact. Record engine/version, capture date, application/deployment version, and baseline revision if known. Do not substitute ORM metadata or SQLite.

When supplied, verify in isolation: (A) empty database provisioning, (B) authoritative existing schema, (C) Alembic upgrade from that schema, (D) API startup, (E) worker startup, (F) representative database write/read, and (G) backup/restore assumptions where evidence exists.

Evidence owner must answer: what creates the initial schema; when Alembic becomes authoritative; which revision represents the baseline; whether Alembic upgrades the existing baseline; whether a new environment reproduces it; and the supported order for provisioning, migration, API, and worker startup.

- **PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
- **POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
- **MIGRATION_REPAIR = BLOCKED**
- **PHASE_5 = NO-GO**

No repair is authorized until this external evidence gate is satisfied.

## EXTERNAL EVIDENCE ACQUISITION — ENVIRONMENT CHECK

Docker/Compose and PostgreSQL tools/server/service are unavailable in the current environment. The repo's PostgreSQL 16 Compose declaration is not a running environment. CI has no PostgreSQL service; development configuration uses SQLite; no staging target is available. No database connection was attempted.

- **POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
- **BACKUP_RESTORE_VERIFICATION = UNAVAILABLE**
- **EMPTY_DATABASE_ALEMBIC_BOOTSTRAP = UNKNOWN (PostgreSQL not run)**
- **EXISTING_BASELINE_ALEMBIC_UPGRADE = UNKNOWN**
- **API_STARTUP = UNKNOWN on PostgreSQL**
- **WORKER_STARTUP = UNKNOWN on PostgreSQL**
- **PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
- **ALEMBIC_TAKEOVER = UNKNOWN for existing baseline**
- **MIGRATION_REPAIR = BLOCKED**
- **PHASE_5 = NO-GO**

External request: provide one of (A) PostgreSQL 16 schema-only dump from authoritative environment, (B) isolated PostgreSQL 16 staging DB matching production baseline, or (C) authoritative schema provisioning artifact. Required metadata only: PostgreSQL version, baseline date/revision, provisioning method, required extensions, Alembic state, and whether source is production/staging/development. No credentials/secrets or application row data are required. After receipt, verify only against an isolated disposable database; do not connect to production or shared DBs.

## PHASE 5 PREFLIGHT — APPLICATION MEMORY BOUNDARY (DESIGN ONLY)

**SLICE = APPLICATION MEMORY PERSISTENCE PORT**  
**SLICE_STATUS = READY** for the bounded code-boundary edit below.  
**PHASE_5 = NO-GO** and **SLICE_EXECUTION = NOT_AUTHORIZED**. This preflight does not certify production persistence or override any external database blocker.

### Inventory, owners, consumers

| Item | Current evidence / consumer | Intended owner and impact |
|---|---|---|
| Domain contracts | `domain/agent_memory.py`: `AgentMemory`, `CorrectionEvent`, `ExecutionLearning`. `domain/memory.py` re-exports these. | Keep `domain/agent_memory.py` canonical; preserve the re-export. |
| Application | `application/memory/memory_service.py` records corrections/learnings, creates IDs/timestamps, redacts values, queries and evicts. `redaction.py` implements recursive redaction. | Remains canonical use-case owner; preserve behavior and constructor keyword `memories`. |
| Concrete persistence import | Memory service imports `repositories.agent_memory.AgentMemoryRepository` directly: confirmed application→repository boundary violation. | Add narrow application-owned protocol with current `create`, `list_for_scope`, and `evict_expired` signatures. |
| SQL adapter | `repositories/agent_memory.py` uses SQLAlchemy `AgentMemoryRecord`, JSON mapping, commits/refresh, tenant-scoped filters, expiry, newest-first ordering and deletion. | Canonical adapter proposed at `infrastructure/persistence/agent_memory_repository.py`; keep old module as re-export. No SQL/query/transaction changes. |
| Composition | `services/container.py` builds repository and `AgentMemoryService`, injects service into `ParameterResolver` and `AutonomousOperationsOrchestrator`. | Change only concrete adapter import; preserve `memories` / `agent_memory` attributes and wiring. |
| Agent consumer | `ParameterResolver` queries only when both workspace and user IDs are present; validates corrections against capability parameter declarations. `RequirementInterpreter` and `RequirementAgent` pass the resolver through. | Keep all agent APIs unchanged. |
| API consumer | Copilot route → `CopilotService.author_workflow` → requirement agent. This call passes `workspace_id=None`; current resolver therefore does not query memory. No direct memory endpoint found. | No API changes; do not describe this path as an active persisted-memory read. |
| Autonomous consumer | Container passes memory service to `AutonomousOperationsOrchestrator`, which optionally calls `record_learning`. No direct API route to this orchestrator found. | Keep optional behavior and `ExecutionLearning` contract unchanged. |
| Worker consumer | `worker.py` builds the shared container. The inspected workflow worker has no direct memory operation. | No worker change; shared container/session construction remains as-is. |
| Compatibility imports | Tests import `repositories.agent_memory`; `domain.memory` is an existing re-export. No external package API was found. | Preserve both paths; treat current repository import as compatibility-sensitive. |

The wider repository placement is transitional, but moving this single adapter into the existing `infrastructure/persistence/` boundary does not imply a broad repository relocation or a `src/platform` move.

### Dependency safety

| Dependency | Classification | Evidence and scope |
|---|---|---|
| Alembic | Optional to the boundary edit; required for deployed memory persistence | Existing revision `c13a7e91d204` creates `agent_memory`, assuming `workspaces` and `users`. No migration will be added/run/changed. |
| Production PostgreSQL schema | Optional to this import inversion; required at runtime for persisted memory | Production schema remains unknown. The existing schema requirement is not removed or newly introduced; no production persistence claim. |
| `create_all()` | Test-only in identified memory tests | `test_agent_memory_repository.py` and `test_agent_memory_integration.py` create SQLite in-memory metadata schemas. Startup/create_all behavior is out of scope. This is not PostgreSQL evidence. |
| DB session/startup | Required transitively to construct current repository/container; unchanged | `Container` uses `make_session_factory`; neither startup nor revision checking changes. |
| Worker startup | Unrelated to a memory operation; shared container construction is transitive | No direct memory call in workflow worker path; do not change worker startup. |
| Cache lifecycle / external providers | Unrelated | No cache or external-provider use in memory service, adapter, or traced consumers. |

This slice requires no Alembic revision, schema change, migration repair, or production database access. It retains the existing `agent_memory` table/model and runtime requirement exactly. If implementation expands into schema/bootstrap/startup changes or cannot preserve old imports, stop and reject the slice.

### Test contract

| Tests | Existing contract protected | Expected after boundary edit |
|---|---|---|
| `tests/test_agent_memory_service.py` | PII redaction; correction/learning mapping; execution reference; scoped query forwarding; TTL and expiry delegation | Identical service behavior through protocol; no test fake contract change. |
| `tests/test_agent_memory_repository.py` | SQL roundtrip; workspace/user isolation; expiry filtering and eviction using in-memory SQLite metadata | Identical adapter behavior; legacy import remains valid. |
| `tests/test_agent_memory_integration.py` | Persisted correction affects requirement parameters; workspace/user isolation | Same combined behavior with canonical adapter and compatibility path. |
| `tests/test_parameter_resolver_memory.py` | Optional service; correction application; rejection of invalid/other-capability values; no query without tenant scope | Unchanged resolver semantics/API. |
| `tests/test_autonomous_operations_orchestrator.py` (memory-specific fake setup around line 525) | Optional learning call to injected service | Unchanged optional orchestration behavior. |

Coverage is adequate for a behavior-preserving dependency inversion and adapter import relocation. It does not establish PostgreSQL production schema compatibility, worker memory execution, or an API memory read. Any new agent-service protocol or consumer interface change would need focused tests before implementation.

### Migration algorithm — design only

**BEFORE:** `application.memory.memory_service` → concrete `repositories.agent_memory.AgentMemoryRepository`; container imports the same class; agents/orchestrator receive `AgentMemoryService`; tests use existing paths.

**TRANSITION:** (1) add `application/memory/ports.py` with a narrow repository protocol; (2) place the unchanged SQLAlchemy implementation in `infrastructure/persistence/agent_memory_repository.py`; (3) retain `repositories/agent_memory.py` as re-export; (4) type `AgentMemoryService` against the port without changing constructor/method behavior; (5) update only the container’s adapter import; (6) keep all consumers and tests on existing import/constructor surfaces.

**AFTER:** agents/application consumers → `AgentMemoryService` → application-owned persistence port → infrastructure SQL adapter → unchanged `database.models.AgentMemoryRecord`. `repositories.agent_memory` remains a compatibility forwarding path.

**Files proposed:** add `application/memory/ports.py`; add/move implementation to `infrastructure/persistence/agent_memory_repository.py`; change `application/memory/memory_service.py`, `repositories/agent_memory.py` (re-export), and `services/container.py` (wiring import). Any implementation must add regression coverage for structural protocol compatibility and preserved import path if existing tests do not prove it.

**Do not touch:** `database/models.py`; `database/migrations/**` or Alembic config/history; startup/revision checks; `worker.py`; API routes/contracts; agent interfaces; domain types/re-export; cache; provider/dependency settings.

**Import order:** define port → establish adapter canonical module plus shim → update service annotation → update composition-root import → run named tests → unchanged full suite. The shim remains available throughout.

**Rollback:** revert the isolated code patch as one unit and restore container import to `repositories.agent_memory`; keep or restore the shim. No persisted data or schema rollback is necessary.

**Future validation commands:** `pytest tests/test_agent_memory_service.py tests/test_agent_memory_repository.py tests/test_agent_memory_integration.py tests/test_parameter_resolver_memory.py tests/test_autonomous_operations_orchestrator.py`, then the unchanged canonical full-suite command. Expected baseline: **193 modules / 977 passed**. No tests were run for this design-only preflight.

### Slice gate

`SLICE_STATUS = READY` applies only to this bounded import/boundary design; it does not resolve the existing global production-schema blocker. `PHASE_5 = NO-GO`. `SLICE_EXECUTION = NOT_AUTHORIZED`.

### Implementation-readiness review correction (2026-10-02)

The design is **implementation-ready with warnings**, subject to the following mandatory test additions and invariants. The earlier statement that the existing coverage alone was adequate is narrowed: service and adapter behavior are covered, but the repository does not currently prove canonical-adapter/legacy-shim identity or memory-specific composition wiring.

**Exact application port contract, derived from current calls:**

```text
create(memory: AgentMemory) -> AgentMemory
list_for_scope(*, workspace_id: str, user_id: str,
               memory_type: str | None = None, key: str | None = None,
               now: datetime | None = None) -> list[AgentMemory]
evict_expired(*, now: datetime | None = None) -> int
```

These are the only three repository operations used by `AgentMemoryService`. Keep the keyword-only filters, optional values, and concrete domain return types. Current adapter behavior has no application-level error translation: SQLAlchemy/JSON/constraint errors propagate. `create` commits, refreshes, then maps the row; `evict_expired` commits and returns the affected-row count; `list_for_scope` reads and returns newest-first, non-expired items scoped by both tenant IDs. The adapter opens/closes its own session per call, so this is not a shared Unit of Work. Preserve these transaction, session, ordering, scope and exception semantics exactly. The port belongs to application because it expresses only what the application use case needs; the memory data/event types and invariants remain domain-owned. No broader persistence abstraction is needed.

**Composition and dependency checks:** `api/main.py` constructs `services.container.Container`; the worker entrypoint `worker.py` calls `build_container`, which constructs the same `Container`. The single memory adapter construction is in `services/container.py`. API routes consume services from that container; no separate API adapter construction was found. Dashboard files contain no memory/repository references. No production script or other non-test caller of `repositories.agent_memory` was found. Tests directly instantiate the adapter and therefore remain compatibility consumers. Agent and autonomous use cases receive `AgentMemoryService`, not the concrete repository. Do not create a new composition path.

**Working-tree caution:** `services/container.py` already has an unrelated local modification to `make_session_factory(...)` arguments (`create_schema` and `require_current_revision`). This is outside the memory slice and must be preserved exactly; only the memory adapter import line should be changed there. The current review made no source edits.

After the change, allowed imports are: `application.memory.memory_service -> application.memory.ports`; `services.container -> infrastructure.persistence.agent_memory_repository` and `application.memory.memory_service`; `infrastructure.persistence.agent_memory_repository -> database.models, domain.agent_memory` (and optionally the application protocol for explicit conformance); `repositories.agent_memory -> infrastructure.persistence.agent_memory_repository` only. The compatibility facade must not be imported by application code. Neither protocol nor adapter may import the compatibility facade. This leaves no cycle: the adapter depends inward on domain/database and, if declared, the application port; the facade only forwards outward to the adapter; the composition root is the only place assembling the concrete graph.

**Minimum test set for implementation:**

1. Existing `tests/test_agent_memory_service.py`, retaining its fake repository and proving the service consumes only the three-method contract (application consumer/protocol test).
2. Existing `tests/test_agent_memory_repository.py`, pointed at the canonical infrastructure adapter for behavior regression; add an assertion that `repositories.agent_memory.AgentMemoryRepository` is the same class object as the canonical adapter (compatibility import test).
3. Add `tests/test_agent_memory_container_wiring.py` proving the composed container uses the canonical adapter and injects the resulting service into the resolver and autonomous orchestrator. Keep database initialization test-local; do not modify shared startup behavior.
4. Existing `tests/test_agent_memory_integration.py` and `tests/test_parameter_resolver_memory.py` for persisted correction, scope, and resolver contract.
5. Existing memory-specific test in `tests/test_autonomous_operations_orchestrator.py` for optional learning behavior.
6. Run the unchanged canonical full suite; expected protected baseline remains 193 modules / 977 passed. Do not run or change tests during this review.

If the compatibility identity or composition test cannot be made without changing public semantics, stop and re-review. Keep database/migration/startup exclusions unchanged. No source changes have been authorized by this review.

## NEXT SLICE SELECTION — POST-MEMORY PREFLIGHT (DESIGN ONLY, 2026-10-02)

**Selection:** `OWNER-SCOPED SYNC-JOB READ API BOUNDARY`. This is the highest-readiness bounded candidate found; it removes the active route's direct repository call by delegating the lookup to the already-wired `application.channels.ChannelSyncService`. It does not consolidate the whole API/repository boundary. Preserve the current compatibility provider `api.dependencies.get_sync_job_repository`; it remains a transitional direct-repository escape hatch for possible internal/external consumers and is not used by the selected route after the proposed change.

**Status:** `READY_WITH_WARNINGS` as design/preflight only. `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`; `PHASE_5 = NO-GO`. No code or tests were changed or run for this selection.

### Readiness-ranked candidates

Ranks reflect only consumer/test/rollback readiness and change-surface size, not business importance.

| Rank | Candidate | Readiness and reason |
|---:|---|---|
| 1 | Owner-scoped sync-job status route: `GET /sync-jobs/{sync_job_id}` | Selected. One API handler delegates to existing application service and already injected `SyncJobRepository`; repository owner filter and API 200/404/error response cases have focused tests. No new composition or schema work. Warning: retain the old dependency getter as compatibility-only transitional coupling. |
| 2 | Owner-scoped channel listing route: `GET /channels` | Viable, but it combines workspace ownership lookup with channel owner filtering and public-field/credential redaction. It needs both use-case delegation and proof that the two existing scope checks remain unchanged. Existing API tests cover owned/unowned workspace and public response fields. |

**Rank 2 candidate record — channel listing API boundary:**

- **CURRENT_OWNER:** route currently performs response mapping in `api/routes/channels.py`, checks workspace ownership through `WorkspaceProjectService`, then reads through `repositories.channels.ChannelRepository.list_for_owner`.
- **CURRENT_CONSUMERS:** `GET /channels` endpoint; `api.dependencies.get_channel_repository` remains a compatibility provider; `ChannelSyncService` also uses the same repository for sync operations.
- **CURRENT_DEPENDENCY_VIOLATION:** active API route directly queries the channel repository after a separate application workspace check.
- **TARGET_OWNER:** an application-owned channel query operation. Reuse the existing `ChannelSyncService` only if the future design accepts channel listing as part of this use-case owner; otherwise a narrowly scoped application `ChannelQueryService` needs explicit justification. Do not place ownership in the API route or repository.
- **EXACT_FILES:** likely `application/channels/channel_sync_service.py` or one justified new application query-service file; `api/routes/channels.py`; `tests/test_api_channels.py`; `tests/test_channel_sync_service.py` or a new query-service test. Retain the old dependency getter as compatibility-only if hidden consumers remain possible.
- **TEST_SURFACE:** existing API tests for owned workspace list, unowned workspace 404, response fields and credential absence; repository owner-scope tests; focused application query test. Preserve channel order as returned by repository.
- **COMPATIBILITY_REQUIREMENT:** unchanged path, query parameter, auth/workspace check, HTTP status and body, `ChannelResponse` shape, field redaction, and `get_channel_repository` symbol.
- **DATABASE_DEPENDENCY:** existing channels/workspaces schema and unchanged repository query; no schema/Alembic change or PostgreSQL access required for a pure delegation.
- **RISK:** MEDIUM due to two independent scope checks (workspace owner and channel owner), response redaction, and service ownership/name fit.
- **ROLLBACK:** restore the route's current repository dependency/call; remove the new application query operation; keep the compatibility provider.
- **WHY_THIS_SLICE_IS_SMALL:** one GET endpoint and one read query with existing API/repository coverage, but it is less bounded than rank 1 because workspace authorization and the canonical application service owner need explicit resolution.

The following tensions are not next-slice candidates because current evidence shows they are broader or behavior-sensitive: application→services authorization/compliance/quota imports are shared across many use cases; remaining application→repository imports include transaction/session handoff (audit, lineage, changesets), so selecting one without specifying its transaction contract is unsafe; `/executions` API access spans two repositories, compatibility routes, report-path access and response mapping; `/data` and `capabilities.cleaning` share legacy quality behavior whose parity is not universal; capabilities→agents includes multiple active validator/QA/extraction collaborators; moving repositories as a tree is not bounded; ORM/domain/database and pandas/scikit-learn ownership is not a single import edge and production schema evidence remains blocked; root `models.*` and `api.schemas` are compatibility re-exports without a justified removal; validator trees retain active fallback/category contracts; execution/workflow/worker consolidation remains constrained by state/recovery/parity semantics; `ai/` has no internal implementation imports found in this scan, while provider use is in active `agents`/container paths, so ownership of legacy empty `ai` packages is unproven.

### Selected candidate record

- **CURRENT_OWNER:** `repositories.sync_jobs.SyncJobRepository.get_for_owner` performs the owner-scoped data lookup; `api/routes/channels.py::get_sync_job` currently orchestrates the HTTP read and 404 mapping.
- **CURRENT_CONSUMERS:** `/sync-jobs/{sync_job_id}` route; `api.dependencies.get_sync_job_repository` provider is also a compatibility surface. The repository is additionally used by `ChannelSyncService` for its sync lifecycle.
- **CURRENT_DEPENDENCY_VIOLATION:** active API route imports/injects `SyncJobRepository` and invokes persistence directly instead of using an application use case.
- **TARGET_OWNER:** existing `application.channels.ChannelSyncService`, which already owns channel sync-job behavior, receives `SyncJobRepository` in the composition root, and is already exposed through `get_channel_sync_service`.
- **EXACT_FILES:** change `application/channels/channel_sync_service.py` (owner-scoped read delegation), `api/routes/channels.py` (use existing service dependency), `tests/test_channel_sync_service.py`, and `tests/test_api_channels.py`. No new source file or composition-root change is needed. Preserve `api.dependencies.get_sync_job_repository` unchanged as a compatibility provider for this slice.
- **TEST_SURFACE:** existing `test_api_channels.py` owner-scoped success, missing/other-owner 404, and error-field-without-credentials cases; existing `test_channel_sync_service.py` fake repository harness plus a new delegation test; existing `test_sync_job_repository.py` owner isolation. Retain all existing sync POST tests and channel-list tests. After implementation, run the unchanged canonical full suite.
- **COMPATIBILITY_REQUIREMENT:** preserve URL, method, auth dependency, response schema/fields, 404 text/status, owner filtering, and the compatibility getter symbol. No request/response/OpenAPI contract change.
- **DATABASE_DEPENDENCY:** existing `sync_jobs`/`workspaces` schema and repository query remain exactly as they are. No schema or Alembic change, production DB access, or PostgreSQL verification is required for the delegation change; tests establish current repository/API behavior, not production schema state.
- **RISK:** LOW–MEDIUM. Main risk is losing owner scoping or changing `None`→404 mapping. A compatibility getter remains an inactive architectural escape hatch, so this does not clear all `api -> repositories` findings.
- **ROLLBACK:** revert the service method and route dependency/delegation; restore the route's prior repository dependency. Leave the compatibility provider in place; no data rollback.
- **WHY_THIS_SLICE_IS_SMALL:** single GET operation, one existing repository method, one already-injected application service/provider, no new composition path, no write semantics, no schema change, and focused unit/API tests already exist.

### Selected target invariant

Active channel sync-job status HTTP handling depends on the application service, not the repository. The application service delegates to the existing owner-scoped repository operation; API output and owner-not-found behavior remain unchanged. The legacy repository dependency getter remains compatibility-only and must not be used by the selected route. `PHASE_5 = NO-GO`; `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.

### Channel listing preflight correction (2026-10-02; design only)

`GET /channels` is still a direct API-to-repository read. Its current behavior is evidenced: authenticate through `get_current_user`; call `WorkspaceProjectService.get_workspace(current_user, workspace_id)` and return 404 before querying on a missing/foreign workspace; call `ChannelRepository.list_for_owner(workspace_id, current_user.user_id)`; repository joins workspace and channel rows, filters both workspace ID and workspace owner ID, orders by `(created_at, id)`, maps ORM rows to credential-free `domain.channel_sync.Channel`; route maps only `id`, `workspace_id`, channel enum value, name, and enabled into the response DTO. Repository retrieval itself does not authorize a workspace; route sequencing establishes that separate check. Current API tests pin authorized response shape/credential exclusion and unowned workspace 404. Repository tests pin cross-owner empty result and credential separation; repository source pins ordering. There is no explicit empty-list route test or assertion that repository access is skipped on failed workspace access.

**Owner decision: D — remain at the current boundary for now.** `WorkspaceProjectService` owns workspace/project access and is not a channel query service. `ChannelSyncService` owns synchronization orchestration and has no listing consumer/contract beyond this route. No other existing application service is evidenced as owner. Adding a one-operation `ChannelQueryService` solely to remove one import would create an abstraction without another demonstrated responsibility/consumer. This is a confirmed API-to-repository boundary tension, but not sufficient evidence to pick an application owner. Do not wire this route through `ChannelSyncService` by convenience. A future preflight must establish a coherent channel catalog/query responsibility (or a second use case) before implementation.

**Compatibility:** retain `api.dependencies.get_channel_repository`; current API tests import and override it. `ChannelSyncService` and container wiring also consume the repository; `tests/test_channel_repository.py` directly imports the implementation. No compatibility path is removed. **Database:** no schema, Alembic, PostgreSQL, or startup work would be intrinsically required for a pure delegation; existing repository query and schema would remain. This does not alter the production database blocker.

If ownership is later resolved and implementation separately authorized, expected limited files are `api/routes/channels.py`, a selected application service or justified new query service, `api/dependencies.py` only if a provider is needed, `services/container.py` only if new composition is needed, and `tests/test_api_channels.py` plus the selected application-service test. Do not change channel models/repository/query, database/Alembic, schema/response DTO, auth/workspace policy, sync operations, compatibility provider, or runtime startup. Minimum added coverage: application operation forwards both workspace and authenticated owner IDs and returns repository results unchanged; route proves no repository call on workspace denial and maps an empty authorized result to `[]`. Preserve ordering, tenant filter, route status/body, response fields, and credential exclusion. Rollback is to restore the route's repository injection/call and remove only the delegation/wiring; no data rollback.

**Preflight status:** `NOT_READY` for implementation because a canonical application query owner is not evidenced. `PHASE_5 = NO-GO`; `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.

## Post-slice architecture reassessment (2026-10-02)

Both the Application Memory Persistence Port and Owner-Scoped Sync-Job Read API Boundary slices are complete. The protected/current accepted suite record is now **194 modules / 981 passed**, four more regression tests than the earlier **193 / 977** baseline (two tests from each slice). This reassessment did not run the full suite.

The memory and sync-job route-specific edges are resolved, but broader `application → repositories` and `api → repositories` edges remain. The API sync-job repository provider and memory re-export remain compatibility surfaces. The channel-listing route still depends directly on its repository. See `POST_SLICE_ARCHITECTURE_REVIEW.md` for the recalculated graph, canonical-owner status, candidate slices and unresolved boundaries.

The two slices changed no schema, Alembic history, startup, deployment or database policy. Therefore `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`, `POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE`, `MIGRATION_REPAIR = BLOCKED`, and `PHASE_5 = NO-GO` remain unchanged. No next slice is authorized: `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.

## Next migration candidate reassessment (2026-10-02; preflight selection only)

`GET /channels` remains deferred: workspace access is owned by `WorkspaceProjectService`, sync orchestration by `ChannelSyncService`, and no existing application service is evidenced as owner of the channel catalog query. Do not create a single-operation service solely to remove its API→repository import.

### Candidate 1 — ChangeSet query persistence port (selected for preflight)

- **Exact edge:** `application.changesets.query_service → repositories.changesets.ChangeSetRepository` (concrete type and instance).
- **Current owner:** `ChangeSetRepository` owns SQL persistence/query implementation; `ChangeSetQueryService` already owns the application list/get/items use cases and tenant owner-ID forwarding.
- **Evidenced target owner:** existing `application.changesets.ChangeSetQueryService`; only its dependency contract should become application-owned. No query behavior or persistence implementation relocation is justified.
- **Consumers:** API `GET /changesets`, `GET /changesets/{changeset_id}`, and rollback endpoint's pre-read all inject `ChangeSetQueryService` through `get_changeset_query_service`; `services.container` constructs it once using `self.changesets`. The rollback service has separate mutation behavior and is out of scope.
- **Exact files likely in implementation:** `application/changesets/query_service.py`; possibly add `application/changesets/ports.py` if a separate protocol module is justified; tests likely `tests/test_changeset_api.py` plus a new focused service test and additions to `tests/test_changeset_repository.py`. `services/container.py` should not need changes if structural typing is used.
- **Existing tests:** `test_changeset_api.py` exercises endpoint mapping, missing-record 404, item response, and rollback lookup using a fake application query service. `test_changeset_repository.py` covers storage, integrity hashes, tamper rejection, apply/atomicity and pointer conflicts, but has no direct coverage found for the three owner-scoped query methods. No direct `ChangeSetQueryService` tests were found.
- **Required new tests before implementation approval:** (1) service contract/delegation tests assert current user ID is forwarded to list/get/items with exact IDs and return values (`None` vs empty list retained); (2) repository owner-isolation tests for get/list/items (foreign owner returns `None`/empty as currently implemented) and preserved list ordering; (3) focused composition/type compatibility proving the existing concrete repository can still be injected without a container behavior change. These tests should be added only under separate implementation authorization.
- **Compatibility surface:** preserve `repositories.changesets.ChangeSetRepository` import/class and all methods, constructor, sessions, transaction behavior, integrity verification, ordering, filters, and return semantics. Preserve API routes, provider symbol, response mapping, and rollback pre-read behavior. No facade removal.
- **Database dependency:** no schema change, Alembic operation, PostgreSQL verification, startup change, or database lifecycle change is needed for a protocol/type dependency inversion. Existing repository tests use local SQLite metadata; they do not prove production schema state. Avoid moving the repository implementation in this slice.
- **Rollback:** revert only the application-owned protocol/type declaration and constructor annotation/import in `query_service.py` (and any dedicated port file/test-only additions); restore the concrete type import. No data or schema rollback.
- **Risk:** LOW–MEDIUM after targeted tests. Main risk is accidentally broadening/narrowing the query contract or changing tenant owner forwarding / absent-vs-empty semantics. Tests currently leave that exact service/repository seam undercovered.
- **Why bounded:** one existing application use case with three read methods and a single concrete dependency; same repository object and runtime wiring; no service relocation or domain/API behavior change.
- **Preflight conclusion:** `READY_FOR_PREFLIGHT`; this is not implementation authorization.

### Candidates rejected for this reassessment

| Candidate | Why not selected |
|---|---|
| API execution detail/history → `WorkflowHistoryService` | The API serves legacy `ExecutionRecord` history/report paths, while `WorkflowHistoryService` serves workflow execution records and performs workflow/RBAC checks. Ownership and behavior are not equivalent; merging them would cross semantics and compatibility routes. |
| Application lineage persistence port | `LineageTrackingService.record_in_transaction` accepts a caller-owned SQLAlchemy session and repository method; replacing that dependency requires a transaction/Unit-of-Work contract. Existing consumers and transaction parity make this less bounded than a read-only ChangeSet query seam. |
| Application audit persistence port | Audit hash-chain lock/read/write operations depend on a caller session and transaction atomicity. This is security/integrity sensitive and not a safe type-only slice without deeper transaction contract tests. |
| API data route → application quality service | `DataOperationsService` and `QualityService` have different legacy behavior/report flows; prior parity evidence does not establish they are interchangeable. |
| Compatibility facade cleanup or container wiring deduplication | Existing shims/providers remain compatibility-sensitive, and no duplicate concrete wiring relevant to an already-established owner was found that safely removes an edge without changing a consumer contract. |

No candidate changes database status: `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`, `POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE`, `MIGRATION_REPAIR = BLOCKED`, `PHASE_5 = NO-GO`, `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`. The accepted 194-module / 981-pass evidence was not rerun here; the full suite was not run.

## ChangeSet query persistence port — implementation complete (2026-10-02)

Implemented only the authorized dependency/type-boundary slice. `ChangeSetQueryService` now depends on the narrow application-owned `ChangeSetQueryPersistencePort` in `application/changesets/ports.py`, containing exactly `list_for_owner`, `get_for_owner`, and `list_items_for_owner` with the existing domain return semantics. `repositories.changesets.ChangeSetRepository`, its path, constructor, query implementations, session behavior, owner filters, ordering, and exception behavior are unchanged. `services.container` still constructs the concrete repository and injects it structurally; API providers/routes and worker composition are unchanged.

Added `tests/test_changeset_query_service.py` for owner forwarding, exact delegation, identity/empty/None preservation, and exception propagation. Extended `tests/test_changeset_repository.py` with owner isolation, missing/empty behavior, and ordering coverage for all three owner-scoped query operations. Existing `tests/test_changeset_api.py` remained unchanged and passed.

**Exact files changed by this slice:**

- Added `application/changesets/ports.py`.
- Updated `application/changesets/query_service.py`.
- Added `tests/test_changeset_query_service.py`.
- Updated `tests/test_changeset_repository.py`.
- Updated this migration record and the current discovery review.

**Validation:** focused service tests **8 passed**; repository tests **12 passed**; existing API tests **6 passed**; combined ChangeSet/application selection **65 passed**. Sandboxed focused runs emitted the known pytest cache permission warning; canonical suite ran outside the sandbox with the exact unchanged command `.\venv\Scripts\python.exe -m pytest -q` and passed **992 in 66.88s**, with no failures, errors, skips, or warnings. `git diff --check` passed for the implementation/test files. Test module count is now **195** (one newly added module); test count is **992**, an increase of 11 over the protected pre-slice **194 modules / 981 passed** (8 new service cases and 3 repository cases).

**Invariant:** ChangeSet query application code depends only on its application-owned three-operation contract. The concrete repository and compatibility import remain in place. No API or worker semantics changed.

`PRODUCTION_SCHEMA_BASELINE = UNKNOWN`; `POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE`; `MIGRATION_REPAIR = BLOCKED`; `PHASE_5 = NO-GO`. This slice provides no evidence that changes those database blockers. No next migration slice was started; `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.

## Post-ChangeSet architecture reassessment (2026-10-02)

The exact canonical suite was rerun per reassessment request: `.\venv\Scripts\python.exe -m pytest -q` → **992 passed in 70.06s**, no failures/errors/skips/warnings. Test tree contains **195** `test_*.py` modules. `git diff --check` exited 0. Existing unrelated dirty worktree paths were observed and left untouched. This is the same 195/992 test count as the just-completed slice verification; no source/test changes were made during this reassessment.

### Current dependency census: application → concrete repositories

| Application module | Concrete repository imports and observed methods | Consumer/owner evidence | Status |
|---|---|---|---|
| `application.audit.audit_service` | `AuditEventRepository`: `lock_workspace`, `get_latest_in_transaction`, `add_in_transaction`, `list_for_owner` | Container; audit API; channel sync and changeset/approval mutation callers use audit recording. Shared transaction/hash-chain semantics. | Defer; security/integrity and caller-session boundary. |
| `application.channels.channel_sync_service` | channel, mapping, sync job/attempt, dataset and project repositories; owner reads, idempotency lookup, create/update, credentials, mapping get/upsert, attempt create, status reload | Container; channel sync API. Multi-aggregate orchestration with writes, idempotency, connector side effects and audit. | Defer; not a single persistence edge. |
| `application.channels.canonical_product_service` | `DatasetRepository.get_for_owner`; also direct `DatasetStorage` and `TabularUploadReader` infrastructure imports | Container → `ChannelSyncService`; dataset projection reads artifact and transforms tabular data. | Defer; storage, upload, and data interpretation boundaries travel together. |
| `application.datasets.dataset_service` | dataset/project/workspace repositories: owner-scoped reads, create, project listing | Container; dataset API and application tools. Also authorization, compliance and quota services. | Defer; multi-repository security/policy and ingestion behavior. |
| `application.workspace.project_service` | workspace/project repositories: create, owner reads/listing, project get/list | Container; studio routes and other application use cases. Also authorization service. | Defer; broad shared ownership boundary. |
| `application.lineage.lineage_tracking_service` | `DataLineageEventRepository`: add, `add_in_transaction`, owner-scoped list | Container; execution capability records events; lineage API reads them. | Defer; public transaction-taking operation and write/read callers need a port contract. |
| `application.workflows.authoring_service` | project/workflow/workspace repositories: owner lookup, workflow/version operations, workspace/project scope checks | Container; workflow API and Copilot authoring consumer. Also authorization service. | Defer; authoring/persistence/security sequence is broader than one operation. |

The ChangeSet query and memory application modules are absent from this concrete repository-import census: they depend on their application-owned ports. The container's concrete repository imports are intentional composition. No generic repository abstraction or repository-tree move is recommended.

### Other layer and API findings

- **Application → infrastructure:** remains in canonical product projection (`DatasetStorage`, `TabularUploadReader`) and Copilot telemetry; QualityService also reaches execution, agents, and `database.models.ExecutionRecord`. These are real concrete dependencies but not one low-risk shared slice.
- **API → repositories:** `GET /channels` listing remains direct; `api/routes/executions.py` directly handles legacy `ExecutionRecord` history/detail/report access with two repositories and filesystem `FileResponse`. No existing application use case has been proven semantically equivalent to all these contracts. Sync-job status is now service-owned.
- **API → services/container:** `/data` clean/extract use `DataOperationsService`, while validate uses `QualityService`; do not merge without parity evidence. `/risk/evaluate` imports the container and calls `build_container()` per request even though `RiskService` is app-owned and wired in the app container. The route's construction reloads `RiskRepository.get_policy()` per request; app-scoped wiring would load policy at application construction. Refresh semantics are undocumented and the route has no direct API test, so defer pending policy-refresh and error/response contract evidence. `api.main → services.container` remains intentional composition.
- **Workflow/API boundaries:** workflow authoring/runtime/history endpoints already use application use cases; execution engine and worker still have separate delivery/state semantics. No workflow execution refactor selected.
- **Other edges:** `capabilities.cleaning → services.data_operations` and capabilities → agents remain active legacy implementation dependencies; execution imports observability infrastructure intentionally. `repositories.channels → application.channels.credential_cipher` remains a concrete inward-direction violation.
- **Services:** `services.container` is the composition root. Authentication/authorization/compliance/quota and validation/data-operation services still combine live business behavior and adapters; no service-wide migration is justified. `services.data_operations` remains used by routes, capabilities, and tests.
- **Persistence/model ownership:** `database/models.py` is the sole observed ORM table declaration site; `models.database` and `models.domain` are re-exports, not duplicate declarations. API DTOs live in `schemas/` with `api.schemas` compatibility re-export. SQL adapters are split between `repositories/` and `infrastructure/persistence/`, but this scan did not establish duplicate implementations for the same table. Keep both trees and database ownership unchanged.

### Prior candidate outcomes and next-slice gate

| Prior candidate | Current status | Evidence |
|---|---|---|
| Application Memory Persistence Port | Resolved | Application service imports application port; SQL adapter remains infrastructure-side; old repository path remains a compatibility facade. |
| Owner-scoped sync-job status | Resolved for the route | Route delegates to `ChannelSyncService`; legacy dependency provider remains, and channel listing still uses repository directly. |
| ChangeSet query persistence port | Resolved | Query service imports only its three-operation application protocol; repository and shared composition remain concrete and unchanged. |
| `GET /channels` listing | Deferred / not ready | No evidenced application owner; prior preflight remains valid. |
| Execution query paths | Deferred / not ready | Legacy execution/report semantics differ from workflow history; API aliases and file delivery remain. |
| Workflow execution paths | Deferred / blocked for consolidation | Worker/sync execution and state/trace/recovery semantics must be preserved; no consolidation boundary evidenced. |
| Dataset/data quality | Deferred / not ready | DataOperations and QualityService have different active endpoint/capability paths and parity is not established. |
| Lineage/audit ports | Deferred | Caller-owned transaction, immutable lineage/audit integrity, and multi-consumer contracts. |

No remaining candidate currently meets all low-risk requirements. `/risk/evaluate` is a plausible future preflight only, not a selected migration candidate: resolve whether persisted risk policy must refresh per request, prove app-scoped composition/error parity, inventory external `get_container` consumers, and add direct API contract coverage first. Other remaining application→repository edges are multi-consumer, security-sensitive, transactional, or mixed with external I/O. Therefore **`NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE`** and **`PREFLIGHT = NOT_READY_FOR_PREFLIGHT`**. No preflight or next slice is authorized.

Gate unchanged: `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`; `POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE`; `MIGRATION_REPAIR = BLOCKED`; `PHASE_5 = NO-GO`; `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.
# Final architecture audit addendum — 2026-10-02

The final audit after three completed bounded slices is recorded in `ARCHITECTURE_CLOSURE_REVIEW.md`. The canonical unchanged suite was run before and after the audit-document edits and reported **992 passed / 195 modules** (final run: 67.63 seconds); the 15-test increase from 977 is explained by the regression tests added by the three completed slices. `git diff --check` passed. This audit changed documentation only.

Completed slices: Application Memory Persistence Port; owner-scoped sync-job status route; ChangeSet Query Persistence Port. Their compatibility facades/providers and concrete persistence behavior remain. Current status remains `NEXT_CANDIDATE=NO_SAFE_NEXT_SLICE`, `PREFLIGHT=NOT_READY_FOR_PREFLIGHT`, `NEXT_SLICE_EXECUTION=NOT_AUTHORIZED`.

Remaining application-to-repository consumers are `application.audit.audit_service`, `application.channels.channel_sync_service`, `application.channels.canonical_product_service`, `application.datasets.dataset_service`, `application.workspace.project_service`, `application.lineage.lineage_tracking_service`, and `application.workflows.authoring_service`. Their transaction, multi-aggregate, policy, I/O, or versioning semantics make them unsafe as a mechanical next port. The route/API, legacy service, quality, capability, risk policy-freshness, plugin, execution-history and compatibility edges are classified with evidence in the closure review. Do not select or execute another slice without a fresh bounded preflight.

Architectural consolidation is separate from production database takeover. Preserve `PRODUCTION_SCHEMA_BASELINE=UNKNOWN`, `POSTGRESQL_RUNTIME_VERIFICATION=UNAVAILABLE`, `BACKUP_RESTORE_VERIFICATION=UNAVAILABLE`, `MIGRATION_REPAIR=BLOCKED`, and `PHASE_5=NO-GO`. No `src/platform` relocation is proposed. Reopen only under the concrete conditions in `ARCHITECTURE_CLOSURE_REVIEW.md`.

## Final migration repair validation closure — 2026-10-02

This section supersedes earlier migration-repair gate statements and test baselines in this planning history. Strategy D is implemented as a single linear active Alembic graph with base/head `20261002_01`; the former 23-revision graph is preserved but inactive in the legacy archive. The canonical PostgreSQL 16 baseline passed a fresh install on PostgreSQL 16.15. The project has only run local/development environments; there is no production database or production data requiring preservation. This does not establish a production schema baseline.

The database operating policy remains a dedicated migration job followed by schema validation and then API/workers. Application startup does not run automatic Alembic migrations. The local disposable database had 31 application tables, 43 FKs (all `NO ACTION`), 67 explicit/application indexes, and 109 total indexes (67 explicit/application + 31 primary-key + 11 unique). Fresh seed policy passed with no demo, admin, or application seed rows. Representative persistence Groups 1–7 passed with INSERT, COMMIT, and fresh-session SELECT.

The former `tests/test_persistence.py` current-head assumption `20260928_01` was stale. That test now obtains the configured active Alembic head and verifies it is `20261002_01`; the obsolete archived `20260926_01 → 20260928_01` active-upgrade/backfill scenario was replaced by a clean active `upgrade head` lifecycle check. Production revision validation was preserved. The canonical command `.\venv\Scripts\python.exe -m pytest -q` passed **994 collected / 994 passed**, with 0 failed, errors, skipped, or warnings, in **75.14 seconds**. `git diff --check` passed.

Architecture closure is unchanged: `ARCHITECTURE_CONSOLIDATION = CLOSED_WITH_DOCUMENTED_DEBT`; `NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE`. No architecture migration is authorized by the green suite. Local migration-repair validation is complete, but production migration safety/readiness is not established because the production Alembic revision and schema baseline are unknown, backup/restore evidence is unavailable, production-equivalent upgrade rehearsal is unavailable, and deployment/provisioning order remains incompletely evidenced.

```text
MIGRATION_REPAIR_VALIDATION = PASS
POSTGRESQL_PERSISTENCE_VALIDATION = PASS_WITH_REPRESENTATIVE_COVERAGE
FULL_REGRESSION = PASS
ARCHITECTURE_CONSOLIDATION = CLOSED_WITH_DOCUMENTED_DEBT
NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
DEPLOYMENT_PROVISIONING_ORDER = INCOMPLETELY_EVIDENCED
```
