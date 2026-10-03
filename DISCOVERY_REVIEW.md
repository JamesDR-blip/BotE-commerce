# Discovery Review — Self-Review Before Migration

> **Final migration-repair closure (2026-10-02):** Strategy D is implemented and locally validated. The active Alembic graph is a single linear baseline with base/head `20261002_01`; the former 23 revisions remain archived/inactive. Fresh install and representative PostgreSQL 16.15 persistence Groups 1–7 passed. The canonical suite passed **994/994 in 75.14 seconds**, with no failures, errors, skips, or warnings; `git diff --check` passed. This does not establish production schema/revision, production-equivalent upgrade, backup/restore, deployment order, or production migration safety. Architecture consolidation remains `CLOSED_WITH_DOCUMENTED_DEBT`; `NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE`; production migration authorization is not established. Historical discovery snapshots below are retained as evidence from their dates and are superseded where they conflict with this closure status.

> **Earlier post-slice status (historical):** This review's architecture findings were supplemented by `POST_SLICE_ARCHITECTURE_REVIEW.md` (2026-10-02). At that time, the accepted evidence was 981 passed across 194 modules. Those architecture edge findings remain useful, but the test baseline and database-repair status are superseded by the final migration-repair closure above.

> **Channel-listing preflight correction (2026-10-02):** `GET /channels` behavior and test boundaries are mapped in `MIGRATION_PLAN.md`. Although the route-to-repository edge is small, no existing application service is evidenced as the canonical channel-list query owner. Keep the route/provider unchanged for now; do not add a single-purpose service solely to erase the import. This candidate is `NOT_READY` until ownership is resolved. No code/tests changed and no full suite was run.

> **Next-candidate reassessment (2026-10-02):** the selected candidate for a separate design/preflight is the existing `ChangeSetQueryService` dependency on concrete `ChangeSetRepository`. Application ownership is already evidenced, but direct service and owner-scoped repository-query tests are missing; the selected status is `READY_FOR_PREFLIGHT`, not implementation authorization. See `MIGRATION_PLAN.md` for consumers, test gaps, rejected candidates, and rollback. `PHASE_5 = NO-GO`; `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.

> **Implementation status update (2026-10-02):** The authorized ChangeSet query persistence port slice is complete. The application query service now depends on the application-owned three-operation protocol; the existing repository implementation/path and composition are unchanged. New service and owner-scoped repository tests close the identified coverage gaps; existing API tests remain unchanged. The full suite passed **992** (195 test modules), with the 11-test increase explained in `MIGRATION_PLAN.md`. This does not change database evidence or the Phase 5 gate.

> **Architecture reassessment before final migration-repair validation (2026-10-02; historical test result):** The canonical suite then reported **992 passed / 195 modules**, and the import census found no safe next migration slice: remaining application→repository edges are transactional, multi-consumer, or policy-sensitive; `/risk/evaluate` is deferred pending policy lifetime evidence. This architecture conclusion remains current; its test count is superseded by the final 994-test validation. See `ARCHITECTURE_CLOSURE_REVIEW.md` and the final addendum in `MIGRATION_PLAN.md`.

**Date:** 29 September 2026

**Scope:** cross-check of `ARCHITECTURE_INVENTORY.md`, `DEPENDENCY_MAP.md`, `OWNERSHIP_MAP.md`, and `MIGRATION_PLAN.md` against Python imports, route dependency providers, the composition root, SQLAlchemy/Alembic wiring, test configuration and checked-in architecture records.
**Change boundary:** no application source, tests, database migrations, or runtime configuration changed; no migration was started. This review was added and `MIGRATION_PLAN.md` received documentation-only corrections to baseline gates, rollback/recovery, and the database safety boundary.

**Refresh status:** the accepted plan for Phases 0–4 has been strengthened against current imports, consumers and named test modules. This is documentary completion only; implementation migrations for Phases 1–4 remain unexecuted.

## Executive assessment

The inventory is directionally accurate and the 977-passing baseline is recorded, but the ownership and migration artifacts are not yet detailed enough to authorize physical consolidation. The dependency map names the important leak patterns but not every concrete importer. This review enumerates the current `application -> services/repositories` and `api -> services/repositories` edges and sets one proposed logical owner for each major concept.

**GO / NO-GO for Phase 5 (physical structure and compatibility classification): NO-GO now.** Phase 5 follows phases 0–4 in the plan, and none of those migrations has been performed. The repository evidence does not yet prove all proposed destination paths or the canonical quality/runtime boundaries. Proceed only after the plan corrections below are accepted, phases 0–4 pass their gates, and moving a given file is supported by consumer evidence. No `src/platform` move is justified or proposed.

## Review of the four artifacts

### 1. `ARCHITECTURE_INVENTORY.md`

- Confirmed: top-level structure and entrypoints match the current checkout; `api/main.py` builds `services.container.Container`, `worker.py` builds the same container, and Alembic reports head `20260928_01`.
- Confirmed: the legacy `ARCHITECTURE_AUDIT.md` is stale relative to current modules, API routes, migrations and sprint notes.
- Correction: the inventory says the successful test run used “normal temp-directory access.” The evidence is more specific: the successful run used elevated filesystem access after sandboxed pytest temp access failed. The result remains **977 passed in 64.27 seconds**; preserve the exact invocation/environment when using it as a future comparison baseline.
- Limitation: path counts and package-level AST counts are useful inventory, not proof that every symbol in a package is active. Dynamic/plugin imports and dependencies outside scanned roots still require call-site tracing before deletion.

### 2. `DEPENDENCY_MAP.md`

- Confirmed: the layer-direction violations are real. The map should enumerate the importers below; “datasets/workflows and other use cases” and “channels routes use repositories” are too broad to serve as migration checklists.
- Classification refinement: `services.container` imported by the composition root is an intentional outer-boundary wiring dependency. The same container exposed to `api/routes/risk.py` is route-level coupling and is transitional. These should not be grouped as one violation.
- Additional confirmed edge: `repositories/channels.py -> application.channels.credential_cipher` is an inward dependency inversion. Move the contract only after identifying who imports and implements it; do not move encryption behavior into the repository.
- Additional uncertainty: `domain` imports pandas (nine import statements) and scikit-learn (one). This weakens the framework/data-library independence claim, but whether those imports belong to domain-quality calculations or a dataframe adapter needs file-level review. Do not move them based only on package names.

### 3. `OWNERSHIP_MAP.md`

The map currently proposes several layer owners in one cell (for example, domain + application + persistence), which describes collaboration but does not satisfy “exactly one canonical owner” for the concept itself. The table below assigns one logical owner to each concept. Supporting use cases, runtime mechanisms and persistence adapters are consumers/adapters; they are not second owners of the concept contract.

| Major concept | One proposed canonical owner for its concept contract | Evidence / limit |
|---|---|---|
| Identity | `domain/identity.py` | Current `CurrentUser` value contract. |
| Authorization | `domain/authorization.py` | Policy/authorization concepts; policy orchestration remains an application use case. |
| Organization | `domain/organization.py` | Organization domain type. |
| Quota | `domain/quota.py` | Quota dimensions/rules; usage persistence is an adapter. |
| Workspace | `domain/studio/workspace.py` | Workspace entity. |
| Project | `domain/studio/project.py` | Project entity. |
| Dataset | `domain/studio/dataset.py` | Dataset entity; upload/profile/storage are separate adapter/use-case concerns. |
| Catalog / mapping | `domain/catalog/mapping.py` | Mapping concepts; channel mapping records are persistence. |
| Data quality | `domain/quality/` | Quality scores/health/anomaly contracts; application service is the execution use case. |
| Validation | `domain/validation/` | Deterministic validation primitives; category plugin contract stays in `plugins`. |
| Capability | `domain/capabilities.py` | Capability contract/value types. |
| Capability dependency | `domain/capability_dependency.py` | Dependency contract and constraints. |
| Capability execution | `domain/capability_execution.py` | Execution result/trace contract; dispatch implementation stays in `execution`. |
| Requirement | `domain/requirement.py` | Typed workflow requirement. |
| Intent resolution | `domain/intent_resolver.py` | Intent domain resolution; agent classification is a consumer. |
| Execution plan | `domain/plans.py` | Plan and step values; serialization is an adapter/helper. |
| Execution context | `domain/execution_context.py` | Context contract. |
| Execution trace | `domain/execution_trace.py` | Trace contract; collector/storage are mechanisms. |
| Workflow | `domain/studio/workflow.py` | Workflow definition. |
| Workflow execution | `domain/studio/runtime.py` | Execution state/value contract; `execution/workflow/engine.py` is the runner. |
| Autonomous operations | `domain/autonomous_operations.py` | Policy/decision contract; application orchestrator coordinates use cases. |
| Approval | `domain/approval.py` | Approval request/decision contract. |
| ChangeSet | `domain/changeset.py` | ChangeSet and snapshot contract. |
| Rollback | `application/changesets/rollback_service.py` | Rollback is a use case, not a standalone persisted domain entity. |
| Risk | `domain/risk.py` | Risk score/decision concepts. |
| Compliance | `domain/compliance.py` | Compliance policy concepts; application use case evaluates them. |
| Audit | `domain/audit.py` | Audit event/chain contract; repositories persist it. |
| Lineage | `domain/lineage.py` | Lineage event contract. |
| Channel synchronization | `domain/channel_sync.py` | Channel and sync-job contracts; connectors implement external IO. |
| Marketplace | `domain/marketplace.py` | Package/type contracts. |
| Rules | `rule_engine/models.py` | Executable rule AST/schema; retrieval/indexing are separate adapters. |
| Plugins | `plugins/base.py` | Validator extension contract; `plugins/registry.py` owns discovery. |
| Agent memory | `domain/agent_memory.py` | Memory/correction/learning concepts. |
| Copilot | `application/copilot/` | Copilot use case; model SDK is an optional provider. |
| Studio | `domain/studio/` | Studio aggregate/value contracts; application packages implement operations. |
| Observability | `infrastructure/observability/` | Logging/metrics/telemetry adapters; business audit remains `domain/audit.py`. |

This is a **proposed logical ownership map**, not evidence that every contract already lives at the proposed file. Before moving or merging modules, verify imports, tests and serialized/persisted forms. Avoid duplicate re-export contracts except explicit temporary shims.

### 4. `MIGRATION_PLAN.md`

- Correct: phases are incremental, avoid destructive schema edits, place high-risk persistence/workflow work after baseline/ownership discovery, and do not require a `src/platform` tree.
- Incomplete: phase gates mention full regression but do not require preserving the exact 977-test collection/result as a pre-merge gate for **each behavior-changing slice**. Add a hard gate: unchanged collection, 977 passing (or explain an intentionally changed test count), no new failures; known baseline/environment failures must be isolated before work begins.
- Incomplete: phases have exit/validation gates, but no explicit per-phase rollback/recovery conditions. Add them before any migration. For code-only refactors use revertable small changes and compatibility shims; for database changes use a restore-tested backup and forward-fix/recovery plan, not blind downgrade.
- Incomplete: destination paths such as `application/ports/*` are proposals, not existing tested architecture. Label them provisional and prove each port with a bounded use case/test before expanding.
- Important distinction: Phase 5 is file ownership/physical structure. It must not begin until the earlier semantic and boundary phases are complete. Defer it indefinitely if no consumer evidence requires physical moves.

## Dependency census: application imports of services and repositories

Static AST scan of all `.py` files under `application/` (excluding `__pycache__`). These are the complete direct `services`/`repositories` imports found in that tree; imports through local aliases or runtime reflection are outside this list.

| Current importer | Direct imported modules | Classification |
|---|---|---|
| `application/approval/approval_service.py` | `services.authorization` | Transitional coupling (B); application use case needs an authorization contract. |
| `application/audit/audit_service.py` | `repositories.audit_events` | Confirmed violation (A); concrete persistence access belongs behind an application-owned port. |
| `application/changesets/mutation_service.py` | `services.compliance` | Transitional coupling (B); preserve compliance decision semantics behind a port. |
| `application/changesets/query_service.py` | `repositories.changesets` | Confirmed violation (A). |
| `application/channels/canonical_product_service.py` | `repositories.datasets` | Confirmed violation (A). |
| `application/channels/channel_sync_service.py` | `repositories.channel_mappings`, `repositories.channels`, `repositories.datasets`, `repositories.projects`, `repositories.sync_jobs` | Confirmed violations (A); five concrete adapters in one use case. |
| `application/datasets/dataset_service.py` | `repositories.datasets`, `repositories.projects`, `repositories.workspaces`; `services.authorization`, `services.compliance`, `services.quota` | Repositories: A. Legacy service imports: B. |
| `application/lineage/lineage_tracking_service.py` | `repositories.data_lineage_events` | Confirmed violation (A). |
| `application/memory/memory_service.py` | `repositories.agent_memory` | Confirmed violation (A). |
| `application/workflows/authoring_service.py` | `repositories.projects`, `repositories.workflows`, `repositories.workspaces`; `services.authorization` | Repositories: A. Legacy service: B. |
| `application/workflows/history_service.py` | `services.authorization` | Transitional coupling (B). |
| `application/workflows/runtime_service.py` | `services.authorization`, `services.compliance`, `services.quota` | Transitional coupling (B); these checks are security/governance gates and must not be weakened or made optional during extraction. |
| `application/workflows/simulation_service.py` | `services.authorization` | Transitional coupling (B). |
| `application/workspace/project_service.py` | `repositories.projects`, `repositories.workspaces`; `services.authorization` | Repositories: A. Legacy service: B. |

Additional directly observed application boundary edges not included in the requested repository/service census: `application/quality/quality_service.py -> database.models.ExecutionRecord`, `-> execution.capabilities.CapabilityExecutionService`, and `-> agents.*`; `application/channels/canonical_product_service.py -> infrastructure.storage/upload`; Copilot modules import agents/telemetry; `application/marketplace` imports rule-engine contracts. These require separate port/provider review and are deliberately not hidden by the census above.

### Application boundary findings

- **A — Confirmed architectural violation:** application imports concrete repository implementations directly in 9 use-case modules (including multiple aggregates in dataset, channel sync, authoring and workspace). Their source rows and consumers are enumerated above.
- **B — Transitional coupling:** four legacy service implementations (`authorization`, `compliance`, `quota`, `data_operations` elsewhere) still serve application/capability behavior. They are live, so keep compatibility while relocating policy/use cases.
- **D — Uncertain:** exact port target modules and whether every repository deserves a separate port cannot be decided from folder structure. Confirm transaction boundaries, query behavior and tests per aggregate before adding interfaces.

## Dependency census: API imports of services and repositories

Complete direct imports under `api/`, including `api.dependencies` because type/provider wiring couples routes to implementations.

| Current importer | Direct imported modules | Classification |
|---|---|---|
| `api/dependencies.py` | `repositories.channels`, `repositories.execution_traces`, `repositories.executions`, `repositories.sync_jobs` | Confirmed route-to-persistence bypasses (A): these repository providers are injected directly into routes. |
| `api/dependencies.py` | `services.authentication`, `services.authorization`, `services.data_operations` | Transitional/legacy service coupling (B); authentication service is a deliberate present auth implementation but not application boundary. |
| `api/main.py` | `services.container` | Intentional outer composition dependency (C) at the application factory; keep at the outermost runtime boundary. |
| `api/routes/channels.py` | `repositories.channels`, `repositories.sync_jobs` | Confirmed bypass (A): list channels and query sync job directly after dependency injection. |
| `api/routes/data.py` | `services.data_operations` | Transitional bypass (B): endpoint directly invokes the older data-operation service. |
| `api/routes/executions.py` | `repositories.executions`, `repositories.execution_traces` | Confirmed bypass (A): route owns history/detail/report queries and response projection. |
| `api/routes/risk.py` | `services.container` | Transitional coupling (B): endpoint obtains risk behavior from the whole composition root rather than an application use case. |

The route import of `domain` types and `schemas` is not included as a service/repository bypass. It remains a separate transport-contract concern. The actual dashboard call path also needs verification before classifying direct service access outside `api/`.

### API boundary findings

- `GET /channels` calls `WorkspaceProjectService` and then `ChannelRepository.list_for_owner`; its ownership check must remain intact when the list query moves behind an application service.
- `GET /sync-jobs/{id}` calls `SyncJobRepository.get_for_owner` directly; preserve owner-scoped 404 behavior and response fields.
- `GET /executions`, `/history`, execution detail, and report download call repositories directly; preserve response caps, aliases, status codes, report format allowlist, report-root security and traces.
- `POST /channels/{id}/sync` already calls `ChannelSyncService`; repository imports are only for other route handlers, so migrate query paths independently.
- `api.main -> services.container` is composition, not a route use case. Do not move it inward to satisfy a simplistic package rule.

## Classification of other identified architecture issues

| Finding | Class | Evidence and review decision |
|---|---|---|
| Concrete app-to-repository imports | **A. Confirmed architectural violation** | AST census above; contrary to stated rule against application depending on concrete repositories. |
| API routes receive concrete repositories | **A. Confirmed architectural violation** | `api.dependencies` providers + route signatures/calls above. |
| `capabilities/cleaning.py -> services.data_operations` | **A. Confirmed architectural violation** | Capability implementation directly calls a legacy service; `services/container.py` wires both. |
| `repositories/channels.py -> application.channels.credential_cipher` | **A. Confirmed architectural violation** | Persistence adapter points inward to application; contract owner must be moved after consumer audit. |
| `application/quality/quality_service.py -> database.models.ExecutionRecord` | **A. Confirmed architectural violation** | Use case imports ORM record type directly. |
| Application use cases -> `agents` | **A. Confirmed architectural violation** | `application/quality/quality_service.py` and `application/copilot/service.py` import agent classes. Expose typed application ports/results or move orchestration to the application boundary; do not make agents authorize operations. |
| Application use cases -> `execution` | **A. Confirmed architectural violation** | `application/quality/quality_service.py` imports `CapabilityExecutionService`; execution dispatch should be called through an application-owned execution port/use case. |
| Application use cases -> `infrastructure` | **A. Confirmed architectural violation** | Imports include telemetry in Copilot and concrete storage/upload adapters in channel product projection. Keep technical implementations outside use cases and inject contracts. |
| API routes/dependency module -> `agents` and concrete `infrastructure.upload` | **B. Transitional coupling** | Copilot routes use agent contracts directly and upload providers expose a concrete reader. Active API behavior is clear; exact application/use-case adapter boundary and upload responsibility need characterization before moving. |
| Route/API reaches domain and transport schemas | **C. Intentional dependency** | Interface layer may map domain contracts to transport models; do not have domain depend back on FastAPI/Pydantic transport. Reduce only where it leaks persistence. |
| Application use cases depend on domain contracts | **C. Intentional dependency** | This is the intended inward direction. Keep business concepts in domain and use cases in application. |
| Repositories depend on `database.models` and map domain values | **C. Intentional dependency** | Persistence adapters are expected to depend outward on ORM metadata and map records to contracts. |
| `services.container` wires application, repositories and infrastructure | **C. Intentional dependency** | Composition is an outer-boundary responsibility. Its location/name may be transitional; the wiring direction is intentional. |
| Infrastructure depends on domain contracts and external SDKs | **C. Intentional dependency** | Adapters may implement/use domain/application ports and depend on technical libraries; domain/application must not import them. |
| Tests call `Base.metadata.create_all` to prepare isolated DBs | **C. Intentional dependency** | Test bootstrap is not itself a production schema owner; preserve explicit test setup when deciding runtime bootstrap. |
| API factory/worker use a shared composition root | **C. Intentional dependency** | `api/main.py`, `worker.py` wire application/adapters at outer process boundary. Composition direction is expected. |
| Application uses legacy auth/compliance/quota services | **B. Transitional coupling** | Live cross-cutting behavior is consumed by multiple use cases; migrate behind contracts without changing decisions. |
| API `data.py` and `risk.py` use legacy services/container | **B. Transitional coupling** | Existing endpoint behavior is active; replace with focused use cases and preserve response/authorization behavior. |
| Validators and plugins cross-import, with plugin registry fallback to `validators/` | **B. Transitional coupling** | README documents plugin-first discovery and legacy fallback; migration must preserve precedence until category-by-category parity. |
| `models/` compatibility imports and root `main.py` | **B. Transitional coupling** | README identifies these as compatibility entrypoints, but external consumers/removal conditions are not proven. |
| `domain/` imports pandas/scikit-learn | **D. Uncertain — requires further evidence** | Confirm module names and whether dataframe/ML logic is the actual business rule. Do not relocate based on library name alone. |
| `ai/` subtree ownership and consumers | **D. Uncertain — requires further evidence** | It exists, but previous ownership document explicitly marks it partly unverified. Enumerate imports/runtime registrations before movement. |
| Quality execution owner among `QualityService`, `DataOperationsService`, workflow/capability path | **D. Uncertain — requires further evidence** | Several active paths and tests exist; no one implementation should be deleted/merged before route-by-route input/output and error characterization. |
| Workflow “duplicate runtime” | **D. Uncertain — requires further evidence** | Code separates application runtime use case from execution engine/queue; package names alone do not prove duplicate business semantics. First document sync and queued state transitions. |

## Persistence and migration boundary: `create_all()` vs Alembic

1. `services/container.py` unconditionally calls `database.models.make_session_factory(settings.database_url)` during container construction. Both `api/main.py:create_app` and `worker.py:create_workflow_consumer` construct this container.
2. `database/models.py:make_session_factory` creates an engine and unconditionally runs `Base.metadata.create_all(engine)` before returning the session factory. No environment flag or “test-only” guard is present in this function.
3. `database/migrations/env.py` separately sets `target_metadata = Base.metadata`; checked-in revisions under `database/migrations/versions` define the Alembic upgrade chain, whose current head is `20260928_01`.
4. Therefore there are currently two schema lifecycle mechanisms: Alembic revisions and unconditional runtime `create_all`. `create_all` creates missing tables but does not apply alterations to existing tables and does not advance `alembic_version`. It is not a safe substitute for upgrades. If invoked against an empty database before Alembic, it can also leave tables that a historical `create_table` revision expects to create.
5. Tests deliberately call `Base.metadata.create_all` and some call `make_session_factory("sqlite://")`; this is a test convenience and separate from production schema lifecycle. README mentions a legacy auto-create path for local/test compatibility, but the code path itself is not restricted to local/test.

**Classification:** the existence of both paths is confirmed; intended environment policy is **D (uncertain)** because docs describe local/test legacy support while current container wiring calls it unconditionally. Treat the production effect as a confirmed persistence-boundary violation (A) until deployment configuration proves otherwise.

**Required handling:** do not remove `create_all` or change Alembic history in an early phase. First enumerate supported database starting states and deployments; test fresh database initialization and upgrade from the supported prior revision; prove unit-test fixtures still work; provide backup and recovery instructions. Any later schema migration must be additive/reviewed and have a restore-tested recovery plan. No destructive database operation is proposed in this review.

## Migration proposals — concrete review records

Target paths below are **provisional** when marked “proposed.” They are architectural hypotheses, not existing modules proven by the repository. Consumers are the direct imports/API entrypoints found above; run reverse-reference and runtime call-site searches again before editing. Each item is a separate, reviewable slice; preserve a compatibility adapter while consumers move.

| Current Path → Canonical Owner → Target Path | Consumers | Migration Action | Risk | Validation | Rollback / Recovery |
|---|---|---|---|---|---|
| `application/*` direct repository imports → application use-case-owned persistence ports → **proposed** `application/ports/` plus existing `repositories/` adapters | audit service, changeset query, canonical product, channel sync, dataset, lineage, memory, workflow authoring, workspace; each target is listed in census | Add a narrow port for one aggregate/use case; adapt current repository behind it; inject at composition. Keep current repository and method behavior. Do not blanket-create generic CRUD interfaces. | Query semantics, owner scoping, transaction ordering, eager/lazy loading and error types can change. | Existing repository and use-case tests; owner/cross-tenant tests; transaction and query-result parity; targeted + full suite baseline. | Revert the isolated adapter/use-case patch; retain direct concrete injection behind existing constructors. No DB change. |
| `application` imports `services.authorization/compliance/quota` → application-owned governance use cases/contracts → **proposed** `application/ports/governance.py` and focused `application/authorization`, `application/compliance`, `application/quotas` | approval, changeset mutation, dataset, workflow authoring/history/runtime/simulation, workspace; see census | First define contract around existing call signatures; keep current services as adapters; move one policy/use case at a time after policy parity review. | Security, tenant scope, quota enforcement, compliance denial and approval eligibility are high impact. | Decision table parity for allow/deny/error; anonymous, cross-workspace, role and quota tests; approval/risk/workflow tests; full 977 baseline. | Revert adapter routing to existing service; preserve prior policy configuration and stored state. Stop rollout on any changed authorization decision. |
| `api/dependencies.py`, `api/routes/channels.py`, `api/routes/executions.py` → focused application query use cases → **proposed** `application/channels/query_service.py`, `application/execution/history_service.py` | API clients of `/channels`, `/sync-jobs/{id}`, `/executions`, `/history`, execution detail, report aliases | Move each query independently; route maps existing results/errors into current schemas; replace repository-typed route dependency with an application service provider. | Contract drift, owner-scope regression, report disclosure/path issues. | OpenAPI snapshot; route tests for owner/cross-owner, 404, caps/aliases/report allowlist; execution trace shape; full suite. | Restore route to old provider without DB changes; retain old methods. |
| `api/routes/risk.py -> services.container` → risk evaluation use case → **proposed** focused application dependency/provider using existing risk service | Risk evaluate route and API contract | Inject the risk use case instead of the whole container; do not reorganize unrelated wiring. | Response status/body and risk threshold differences. | Risk domain/service tests and API response contract tests. | Restore previous route wiring; no persisted state changes. |
| `api/routes/data.py` and `capabilities/cleaning.py -> services.data_operations` → one characterized quality/cleaning application use case → **proposed** `application/quality/cleaning_service.py` or existing `application/quality` if semantics match | Data API, cleaning capability, container, workflow chain and any dashboard facade | First trace exact endpoint/capability behavior and determine if they are equivalent. Delegate old entrypoints to selected use case; preserve ordering and outputs. Do not delete `DataOperationsService` until consumer census is empty. | High: cleaning/autofix/validation order, reports, extraction, metrics and error mapping may differ. | Golden input/output comparisons per entrypoint; API status/body; capability trace; quality/workflow integration; full suite and unchanged 977 collection. | Repoint facade/route to previous `DataOperationsService`; retain implementation and prior report/artifact behavior. No data rewrite. |
| `repositories/channels.py -> application.channels.credential_cipher` → provider-neutral credential cipher port → **proposed** `application/ports/credential_cipher.py` or domain shared contract, final location after consumer audit | Channel repository, channel service/container, credential tests, connectors | Move only the interface; keep Fernet encryption and key handling in `infrastructure/security`; inject adapter. Preserve ciphertext format and key source. | Secret exposure, unreadable credentials, accidental re-encryption/data loss. | Cipher round-trip with existing ciphertext fixtures, key-rotation tests if present, channel repository/connector tests; never print credential material. | Keep old import as shim to the new protocol; revert injection while preserving encrypted bytes and secrets unchanged. No bulk re-encryption. |
| `application/quality/quality_service.py -> database.models.ExecutionRecord` → quality use-case persistence port → **proposed** `application/ports/executions.py` implemented by current repository | Quality service, reports/execution APIs, composition and tests | Replace ORM type access with an application result/protocol; map current repository record at adapter boundary. Confirm which fields are public/persisted first. | Data/result shape and persistence timing can change. | Persistence serialization round-trip, execution/detail/report API, failure rollback behavior, full suite. | Restore old type mapping; no schema change. |
| `database/models.py:make_session_factory -> Base.metadata.create_all` plus Alembic versions → one Alembic-owned deployment schema lifecycle; explicit test schema fixture → **proposed** `database/session.py` / test fixture (target provisional) | `services/container.py`, API/worker startup, persistence/repository tests and local setup docs | First split engine/session construction from schema initialization. Only after fresh/upgrade workflows are proven, remove runtime `create_all` from production construction while retaining explicit test fixture bootstrap if needed. Do not edit applied revision history or drop data. | Highest database operational risk: empty DB startup, partial/legacy schemas, worker boot, stale `alembic_version`; schema drift. | Fresh DB via `alembic upgrade head`; upgrade from every supported predecessor; compare schema; app/worker startup with migrated DB; tests with explicit fixture; backup restore rehearsal. | Keep prior startup behavior available behind a temporary explicit dev/test bootstrap while rolling back application code; restore from verified backup for schema faults. Do not run blind Alembic downgrade; no destructive migration in this phase. |
| `application/quality/quality_service.py -> agents/execution`, `application/copilot/service.py -> agents`, channel product use case -> `infrastructure.storage/upload`, Copilot -> telemetry → application-owned orchestration/contracts → **proposed** `application/ports/{quality,planning,execution,storage}.py`; implementations remain under `agents/`, `execution/`, `infrastructure/` | Quality route/capability and persisted execution flow; Copilot service/route; canonical product projection; telemetry | Replace concrete collaborator imports with only the contracts each use case needs; move provider construction to composition. Keep deterministic permission and execution policy in application/domain. | Output schema, execution ordering, provider availability, telemetry gaps, upload safety behavior. | Existing Copilot/quality/execution tests; fake provider/adapter tests; upload formula/size/path safety checks; trace/log parity; full 977 baseline. | Revert one collaborator at a time to the currently injected implementation; keep old constructors and adapter classes until consumers migrate. No storage rewrite. |
| `api/dependencies.py -> infrastructure.upload`, `api/routes/copilot.py -> agents` → application-facing upload/Copilot use cases → **proposed** `application/datasets/` and existing `application/copilot/` contracts | Data upload route, Copilot route and DI providers | Change route dependency from concrete adapter/agent to application contract and map existing errors/contracts | Upload size/path/formula behavior or Copilot response/tool behavior could shift. | Upload malformed/oversized/formula tests; Copilot contract/authorization/tool tests; OpenAPI snapshot; full suite. | Restore existing route providers and adapters; preserve response and input behavior; no data mutation. |
| `validators/` + `plugins/registry.py` compatibility fallback → `plugins/` extension contract/registry → category modules remain in place until migrated; per-category target in `plugins/<category>/` | validator registry, validation capability, category tests, rule engine | Move one category implementation at a time; preserve plugin-first registration/fallback ordering until all callers prove parity. | Validator precedence/autofix/rule behavior changes. | Per-category input/output/error/autofix parity and dynamic discovery tests; full suite. | Restore prior validator module/fallback registration; keep shim, do not remove old category. |
| `models/*`, `controllers/*`, `views/*`, root entrypoints → existing canonical domain/database/api/app owners → physical file targets determined per file after Phase 0; **no `src/platform` target** | Internal imports, documented launch commands, tests and unmeasured external consumers | For each file, record importer set and compatibility window; move only if it removes a demonstrated ambiguity; add a shim only with owner, target and removal condition. | Import/API/launch breakage and unobserved external consumers. | Repository-wide import scan, compile/import checks, documented API/worker/dashboard startup, test suite, shim usage telemetry or explicit deprecation evidence. | Revert file move and keep compatibility import/entrypoint. No schema or data mutation. |
| `domain` pandas/scikit-learn use and `ai/` subtree → unresolved until ownership is proven → **no target path approved** | Domain quality modules, runtime AI/provider imports; exact consumers not yet enumerated | Investigation only: map imports, public types and test behavior. Do not perform code migration based on the current inventory. | Numerical changes, provider coupling, optional dependency/runtime changes. | Call-site inventory, behavior parity tests, import/startup checks, provider fakes. | No migration has started; retain current files/dependencies. |

## Phase 0–4 documentation completion and remaining blockers

The requested documentary corrections are now recorded in the five discovery files:

1. `DEPENDENCY_MAP.md` contains the complete current AST census for application/API imports of services/repositories and distinguishes route imports from composition.
2. `OWNERSHIP_MAP.md` has one proposed concept-contract owner per major concept; multi-layer collaborators are explicitly not second owners.
3. `MIGRATION_PLAN.md` protects the accepted 977/977 baseline, maps proposed order to direct consumers and existing test modules, gives per-phase recovery actions, and marks all unproven physical paths as proposals.
4. `MIGRATION_PLAN.md` records the `create_all`/Alembic relationship and prohibits destructive schema/data changes in early phases.
5. Unresolved runtime/database/dashboard/AI/domain-library questions are listed in the plan and map; they remain blockers only for slices that depend on them.

These changes do not mean implementation Phases 1–4 are complete. No source migration was performed under the user's instruction. Phase 0 documentation is current; phase gates requiring CI guards, code migrations, runtime/database checks and rollback execution remain future implementation work.

## PHASE 5 ENTRY CRITERIA

The authoritative checklist is in `MIGRATION_PLAN.md` under this exact heading. Phase 5 stays **NO-GO** until every checkbox is satisfied. In particular, Phases 1–4 must first be executed and pass the protected baseline; the quality and workflow/capability paths must be proven with consumer parity; every file must have a consumer/test/rollback record; `create_all`/Alembic startup policy must be decided; and no physical move may rely on an unproven destination. The discovery documents alone do not satisfy implementation gates.

## Final GO / NO-GO assessment

**NO-GO to Phase 5 now.** Phase 5 is a later physical consolidation phase, not the next safe action: Phases 1–4 implementation work remains unexecuted, the exact canonical quality path is unproven, the `create_all`/Alembic environment policy is unresolved, and external/runtime consumers for some legacy trees are unknown. Moving files now would encode unverified architecture and add avoidable compatibility risk.

## PRE-MIGRATION VERIFICATION — repository evidence only (2026-09-29)

No implementation, tests, database migrations, runtime configuration, or schema were changed. No Phase 5 migration started. The protected baseline remains the previously verified **977 passed** (193 modules, `.\venv\Scripts\python.exe -m pytest -q`, 64.27 seconds); this read-only verification did not rerun the suite. See `MIGRATION_PLAN.md` → “Pre-migration verification addendum” for call graphs, test crosswalk, and the required Phase 5 entry matrix.

### Evidence-backed conclusions

| Topic | Evidence-backed decision / classification | Limits |
|---|---|---|
| Quality path | **RESOLVED** — `application.quality.QualityService` owns upload validation use case; `execution.capabilities.CapabilityExecutionService` dispatches; `capabilities/` hosts registered operations; `domain.validation` and `domain.quality` own validation/quality calculations. `DataHealthService` is a distinct persisted-health use case. | Test coverage does not prove parity for every category, route, workflow, plugin precedence, errors, reports and traces. Migration parity remains blocked. |
| Quality legacy coupling | **B. Transitional coupling** — direct `/clean` and `/extract` use of `DataOperationsService`; `CleaningCapability` also delegates cleaning to that service. `validators/` remains a live registry fallback for some categories; `validators.fashion` is a re-export shim. | Do not remove fallback or service until per-consumer parity is tested. |
| Validation/domain primitives | **C. Intentional dependency** — `domain.validation` primitives are consumed by category validators and rule evaluation; they represent reusable validation logic rather than infrastructure I/O. | Exact category migration and plugin precedence still need tests. |
| Workflow ownership | **RESOLVED** — `domain.studio.workflow.Workflow` is the definition; `WorkflowRuntimeService` is the API use case; `WorkflowEngine` is engine; Redis/in-process queue transports execution IDs; DB state is authoritative. | This resolves ownership, not failure/retry equivalence. |
| Sync/worker business semantics | **RESOLVED, bounded** — with production wiring and risk gate, both paths execute the pinned version through `execute_existing` and shared streaming/runtime logic. Sync returns inline; async returns queued state and adds transport/claim/ack semantics. Risk/authorization/compliance/quota gates run in API application use case, not worker. | Exact failure/recovery parity is **BLOCKED**: worker process death after `QUEUED → RUNNING` may leave a stale running record; replay can be acknowledged after a failed claim. No stale-running reconciler was found. Existing tests do not prove recovery at this crash point. |
| Database lifecycle | Production-reachable `create_all()` is **RESOLVED as a code fact**; its deployed use and supported database starting states are **BLOCKED**. `make_session_factory` unconditionally calls it; API and worker container construction call the factory. Alembic has 23 revision files and current single head `20260928_01`; README/runbook describe deployment upgrades, but Docker startup does not run Alembic. | Proposed policy is Alembic authoritative for application schemas; explicit fixtures own isolated test bootstrap. This proposal does not itself resolve the present runtime conflict. `create_all` can create missing tables but does not alter existing columns or stamp Alembic state. Empty/partial DB coexistence is unproven. The runbook's stale `20260923_01` reference was corrected after checking `alembic heads`. No DB change is authorized. |
| Dashboard | **RESOLVED in repository** — root `dashboard.py` is active Docker/Compose/README launcher and delegates to `app.dashboard`; UI uses HTTP `DashboardApiClient`, not DB/repositories. | Tests cover mocked client methods, not rendered Streamlit or deployed E2E. Keep launcher; external invocation unknown. |
| AI/agents | **RESOLVED in repository** — active behavior resides in `agents/` and `application/copilot/`; container conditionally wires optional Copilot model; routes consume Copilot. `ai/` packages inspected are empty initializers with no in-repo consumer. | External imports of `ai/` cannot be excluded. Provider-connected behavior is not covered by fakes. No delete/move approval. |
| controllers/views | **RESOLVED in repository** — inspected `controllers/` and `views/` trees contain only empty initializers and no in-repo consumer. | External use unknown; retain until deprecation evidence exists. |
| Compatibility modules | `models/database.py`, `models/domain.py`, `api/schemas.py`, root `main.py` have re-export/launcher behavior; docs identify compatibility surfaces. Root `main.py` is documented; root dashboard launcher is actively used. | Internal absence of imports is not evidence of no external users. Keep shims/launchers. |
| pandas | **RESOLVED** — pandas has domain, application, infrastructure, capability, validator, agent, API and dashboard imports. DataFrame semantics belong to the cross-layer tabular quality/validation subsystem; parsing stays infrastructure, orchestration application, presentation dashboard. | Preserve DataFrame types/order/index/dtype/null and streaming contracts. Not a single-layer dependency. |
| scikit-learn | **RESOLVED at responsibility level; implementation boundary BLOCKED** — `IsolationForest` is used by `domain.quality.anomalies.detect_anomalies`, called by runtime QA, so anomaly/quarantine semantics belong to quality. | Tests/evidence do not establish whether sklearn implementation should remain in domain or move behind a quality adapter. Pin seed, threshold, quarantined rows, score/report output before relocation. |
| Physical targets | **RESOLVED** — no target path is approved merely by proposal. No `src/platform` move is justified by this evidence. | Keep every physical target provisional until a bounded slice proves it. |

### Classification register

These classifications concern observed architecture, not a claim that every architecture issue has been fixed:

- **A. Confirmed architectural violation:** existing application-layer imports of concrete persistence/framework/service/infrastructure details documented in this review's earlier dependency census remain confirmed violations. They have not been changed. No new source violation was created by this read-only work.
- **B. Transitional coupling:** quality facade/service usage (`DataOperationsService`), active validator fallback/registry precedence, concrete workflow policy collaborators, API route repository/container bypasses, compatibility re-export and launcher modules. These are active paths to preserve while boundaries are migrated.
- **C. Intentional dependency:** domain validation/quality logic consumed by capabilities; workflow engine used by application runtime and worker; queue transporting persisted execution IDs; dashboard using server HTTP API; explicit test fixtures creating isolated schemas; application-owned Copilot tool allowlist and optional provider wiring.
- **D. Uncertain — requires further evidence:** deployed database initialization state and `create_all`/Alembic coexistence; workflow stale-RUNNING recovery; external importers of compatibility paths; all-category quality parity; Streamlit render/deployed E2E; provider-connected Copilot/agent behavior; sklearn adapter boundary and numeric parity.

## PHASE 5 ENTRY REVIEW

Every blocker below is explicitly classified. **RESOLVED** means repository evidence established the present owner/path or bounded behavior; it does not by itself mean a file move is ready. Any remaining `BLOCKED — EVIDENCE REQUIRED` keeps Phase 5 NO-GO. See the matrix in `MIGRATION_PLAN.md` for current/canonical owner, consumers, tests, risk, required parity and rollback per concern.

| Entry question / blocker | Status | Repository evidence and remaining requirement |
|---|---|---|
| Canonical upload quality/data-quality owner and actual runtime path | **RESOLVED** | `api/routes/data.py`, `application/quality/quality_service.py`, container registration, capability specs/implementations and `services/validation_service.py` establish `QualityService → CapabilityExecutionService → clean/validate/QA` path. `DataHealthService` is separate. Preserve direct `/clean`/`extract` legacy facade during parity work. |
| Quality behavior parity across direct API, workflows, validators and plugins | **BLOCKED — EVIDENCE REQUIRED** | Existing unit/integration tests cover representative paths, not every category, result/error/report/trace/autofix ordering or plugin-first fallback. Add characterization/parity evidence before changing consumers. |
| Canonical workflow definition/use case/engine/worker/queue roles | **RESOLVED** | Domain Workflow, `WorkflowRuntimeService`, `WorkflowEngine`, worker class and Redis queue code establish present responsibilities. |
| Sync vs worker execution and policy parity | **BLOCKED — EVIDENCE REQUIRED** | Shared engine path in normal production wiring is verified, but lifecycle differs; policy gates are API-side. Need contract tests for all gates and lifecycle invariants. |
| Worker retry/crash recovery and rollback | **BLOCKED — EVIDENCE REQUIRED** | `WorkflowExecutionWorker.run` returns on failed claim; Redis consumer acknowledges normal worker return. No stale-RUNNING recovery found. Define and test handling of process death after claim before terminal state, duplicate delivery and replay before migration. |
| Relationship of `make_session_factory`, `create_all`, Alembic, API/worker startup, tests | **RESOLVED as code topology** | `database/models.py`, `services/container.py`, `api/main.py`, `worker.py`, Docker commands, Alembic config/history and explicit test setup were inspected. Runtime `create_all` is reachable in production API/worker construction and is unconditional. |
| Authoritative database policy and safe supported starting states | **BLOCKED — EVIDENCE REQUIRED** | Recommend Alembic as authoritative app schema lifecycle and explicit test-only `create_all`; actual deployment starting states and fresh/existing/partial coexistence are not evidenced. At the time of this review, the rollback runbook still carried a stale `20260923_01` head reference; it was corrected to `20260928_01` on 2026-10-02. Before bootstrap change: reviewed policy, supported-state matrix, fresh and predecessor upgrade checks, API/worker startup, schema comparison and backup restore rehearsal. |
| Dashboard runtime owner and consumers | **RESOLVED in repository** | Compose/Docker/README call root launcher; it delegates to `app.dashboard`, which uses HTTP client. Tests cover mocked client only. |
| Dashboard visual/deployed consumer behavior | **BLOCKED — EVIDENCE REQUIRED** | No render/deployed end-to-end test found. Keep existing launcher and client contracts until launch and HTTP behavior are checked for a relevant move. |
| Active AI/Copilot owner | **RESOLVED in repository** | Container/routes wire `application/copilot` and `agents`; `ai/` is empty scaffold in this tree. |
| External consumers of empty/compatibility modules and provider-connected behavior | **BLOCKED — EVIDENCE REQUIRED** | Repo scan cannot prove absence of external imports. Optional-provider runtime is not covered by mocked provider tests. Retain all shims/modules until explicit external/deprecation evidence. |
| pandas quality/validation ownership | **RESOLVED** | Cross-layer import and call sites demonstrate tabular data as a platform contract; layer responsibilities are identified. |
| sklearn implementation placement and numeric parity | **BLOCKED — EVIDENCE REQUIRED** | Quality responsibility is clear; current test evidence does not prove threshold/seed/quarantine/score parity for an adapter move. Keep existing implementation. |
| Physical target paths and `src/platform` | **RESOLVED** | Current repository evidence does not justify a broad `src/platform` move; every physical path remains a proposal pending per-slice ownership and consumer evidence. |
| Rollback condition for each selected migration slice | **BLOCKED — EVIDENCE REQUIRED** | General reversible-code rollback is documented, but chosen files need explicit importer rollback and workflow replay/DB recovery conditions. Schema work additionally needs restore-tested backup. The matrix records minimum per-concern recovery; it is not a tested operational rollback. |
| Protected baseline and Phases 0–4 completion | **BLOCKED — EVIDENCE REQUIRED** | Baseline evidence is preserved as 977 passed; this turn did not rerun it. Phases 0–4 source migration and gates remain unexecuted. Phase 5 cannot start on discovery evidence alone. |

### Exact Phase 5 entry conditions

All conditions are cumulative; any unmet item is NO-GO:

1. Complete and record the authorized Phases 0–4 work; discovery documents alone do not count as implementation completion.
2. Immediately before the first Phase 5 slice, reproduce unchanged collection and **977 passed**, explain all warnings, then repeat targeted and full protected gates after each slice.
3. Select an exact file slice with evidence-backed canonical owner, complete repository/runtime consumers, test coverage, external compatibility decision, physical target justification, validation gate and actionable rollback/recovery condition.
4. Establish quality parity for direct API, workflow/capability, all migrated categories, plugin precedence, ordering, errors, autofix, reports, persistence and traces.
5. Establish workflow sync/worker parity for pinned version, state transitions, authorization/compliance/quota/risk/approval, idempotency, duplicate delivery, failures, streaming, traces and a tested recovery policy for stale `RUNNING` records.
6. Obtain an evidence-backed and reviewed database lifecycle policy; identify supported fresh/existing/partial states; verify Alembic fresh/upgrade paths, schema equivalence, API/worker startup and backup restore before any bootstrap change. No destructive migration may accompany structural work.
7. Verify dashboard launcher and relevant HTTP behavior; preserve documented root launchers. Keep AI/compatibility shims where external use is unknown, or obtain explicit deprecation/consumer evidence.
8. Pin pandas DataFrame and sklearn anomaly/quarantine/score behavior before relocating implementations or dependencies.
9. Prove every proposed target by a bounded preceding slice. Do not introduce `src/platform` without separate measured repository evidence.
10. Resolve or explicitly accept each relevant security, public contract, ownership, data integrity and operational recovery question in a reviewed decision record. No unresolved critical runtime path or undefined rollback may remain.

### Final assessment and recommended first slice

**Phase 5: NO-GO.** Confirmed ownership decisions narrow the future work but do not satisfy migration gates. The hard blockers are quality parity breadth, workflow stale-running crash recovery, production-reachable schema auto-creation versus Alembic policy and supported startup states, external compatibility/provider evidence, sklearn numeric parity, and unexecuted Phases 0–4/baseline refresh. No source migration should begin under this assessment.

If a later authorized migration proceeds after its gates, the plan still recommends the smallest initial Phase 1 experiment: `application/memory/memory_service.py` behind the existing `repositories.agent_memory` boundary, validated by `test_agent_memory_service.py`, `test_agent_memory_repository.py`, `test_agent_memory_integration.py`, then the complete 977-test baseline. This is a recommendation only and is not Phase 5 authorization.

## BLOCKER RESOLUTION PHASE — initial baseline stop (historical; superseded below) (2026-09-29)

The blocker-resolution request requires stopping if the refreshed baseline differs from 977. The canonical command was run first: `.\venv\Scripts\python.exe -m pytest -q` using Python 3.13.15 (64-bit), Windows 11 build 26200, pytest 9.1.1, executable `D:\Autonomous_E-commerce_Data_Operations_Platform\venv\Scripts\python.exe`. It completed in **99.80 seconds** with **874 passed, 0 failed, 103 errors, 0 skipped, 2 warnings**. The outcomes sum to 977 cases; this run did not separately report module count. The accepted prior baseline remains 193 modules and 977 passed; the failed refresh does not replace it.

**Difference classification: ENVIRONMENT-RELATED, high confidence.** Captured representative pytest setup errors show `PermissionError: [WinError 5] Access is denied` from the `tmp_path` fixture at `C:\Users\Admin\AppData\Local\Temp\pytest-of-JamesDR`. This blocks fixture setup for a subset of tests. The output does not establish an implementation regression. Per the explicit stop condition, the suite was not rerun with elevated access or a changed temp location; focused quality/worker tests were not run; no production or test code was modified. All test-dependent work in this phase is paused until baseline reproducibility is restored.

| Blocker | Status | Evidence | Remaining risk | Required action before Phase 5 |
|---|---|---|---|---|
| Refreshed protected baseline | **RESOLVED — RECONFIRMED** | Historical sandbox run produced 874 pass / 103 setup errors. The same canonical command later ran outside the sandbox: 977 passed in 64.81s, no warnings summary; isolated `tmp_path` test passed outside sandbox. | Sandbox execution still cannot write its temp/cache paths; it must be granted access or tests run in a permitted process context. | Preserve 193 modules / 977 passed; use an environment with authorized writable pytest temp/cache paths. No ACL or test changes. |
| Quality parity across upload, category validators, plugin precedence, clean/validate/QA, reports/errors/traces and workflow consumers | **PARTIAL** | Existing evidence in preceding review: `QualityService`, capability registrations, validator registry and route wiring; representative named tests in `MIGRATION_PLAN.md`. No new focused tests were run after baseline mismatch. | Category-wide output/error/order/report/trace parity remains unproven. | After baseline is restored, run/add focused tests for direct API and workflow/capability paths, plugin-first/fallback precedence, and report/error/trace contracts; record PROVEN/PARTIAL/UNKNOWN by behavior. |
| Worker failure recovery | **PARTIAL** | `WorkflowExecutionWorker.run` claims then calls `execute_existing`; Redis consumer acknowledges when worker returns; prior repo inspection found no stale-RUNNING reconciler. Existing worker/async tests named above do not cover process death after claim. | Persisted RUNNING work may not be reclaimed; production impact/recovery policy untested. | After baseline is restored, add/run a focused failure-lifecycle test. Document the observed gap; do not redesign recovery in this phase. |
| `create_all()` / Alembic safety | **PARTIAL / BLOCKED** | `make_session_factory` unconditionally calls `create_all`; API and worker container construction reach it; `alembic heads` confirmed `20260928_01`. The runbook's stale `20260923_01` reference was corrected in this documentation pass. | Actual deployed DB state, migration order, coexistence on fresh/partial schemas and restore process are not evidenced. | Repository evidence must define supported fresh/upgraded state and exactly when startup invokes `create_all`; deployment operator evidence is needed for actual DB state. No inferred safety. |
| Compatibility consumers | **PARTIAL** | Repo scan classified root dashboard launcher as ACTIVE; `app.dashboard` is its UI; active AI is `agents`/`application/copilot`; inspected `ai`, `controllers`, `views` include empty scaffold; compatibility re-exports/launchers exist. | External consumer inventory and provider-connected behavior cannot be established from internal references alone. | Preserve unknown modules/shims. Classify each as ACTIVE, LEGACY BUT PROTECTED, PROVEN INTERNAL ONLY, EXTERNAL UNKNOWN, or SAFE TO DEPRECATE only with positive deprecation evidence; do not infer safe deletion. |
| scikit-learn parity | **PARTIAL** | `domain/quality/anomalies.py` imports `sklearn.ensemble.IsolationForest`; QAAgent calls `detect_anomalies`; outputs affect quarantined rows and quality results. | Test coverage of exact seed/threshold/quarantined indices, persistence/serialization, and numeric output was not run or established in this phase. | After baseline recovery, test current inputs/outputs/callers and pin deterministic anomaly set plus resulting score/report behavior before any relocation. |
| Phase 5 gate | **BLOCKED — NO-GO** | Baseline is reconfirmed, but quality, worker, schema and compatibility blockers remain partial/unknown and Phases 0–4 implementation gates remain unexecuted. | Critical behavior/recovery/database/consumer boundaries remain unresolved. | Satisfy every exact entry criterion in this review and `MIGRATION_PLAN.md`; passing tests alone does not make Phase 5 GO. |

The stale runbook head was verified against `alembic heads` and corrected to `20260928_01`; this reconciles documentation only and makes no claim about deployed database state. No Phase 5 migration started.

## TEST ENVIRONMENT RECOVERY — baseline reconfirmed (2026-09-29)

The original sandbox run is retained above as historical evidence. Diagnosis found `pytest.ini` contains no `basetemp` or cache override; `TEMP` and `TMP` resolve to `C:\Users\Admin\AppData\Local\Temp`, and `tempfile.gettempdir()` uses that directory when it exists. A minimal existing test, `.\venv\Scripts\python.exe -m pytest -q tests/test_api_marketplace.py::test_install_signed_rule_pack_endpoint`, failed in the sandbox with the same `tmp_path` `PermissionError: [WinError 5]`. A pre-created repo-local temp directory also failed under the sandbox. The same test passed outside the sandbox (1 passed in 1.78 seconds).

Read-only ACL inspection confirmed the current Windows identity `JAMESDR\JamesDR` owns the Temp root, failing `pytest-of-JamesDR`, and inspected repository pytest temp/cache directories; the owner has FullControl/OWNER RIGHTS FullControl. No permissions or pytest configuration were changed. This establishes the sandbox filesystem restriction as the cause; there is no evidence requiring an external Windows ACL modification. The least invasive remediation is to run tests in an approved process context with access to existing temp/cache paths, or grant the sandbox process access to an isolated writable path.

The unchanged canonical command `.\venv\Scripts\python.exe -m pytest -q` then ran outside the sandbox with no environment or pytest option overrides: **977 passed, 0 failed, 0 errors, 0 skipped, 0 warnings reported in 64.81 seconds**. The accepted **193 modules / 977 passed baseline is RECONFIRMED**. `alembic heads` reported `20260928_01`; the stale `20260923_01` references in `docs/operator/database-migration.md` were corrected as a documentation-only change. No quality or worker tests were run after this baseline because this task requires stopping at baseline verification. Phase 5 remains **NO-GO** for the other blockers documented above.

**GO only for the documentary Phase 0–4 planning package.** Implementation of phases 1–4 must use the bounded sequence and gates in `MIGRATION_PLAN.md`; a broad `src/platform` relocation is not justified by this repository evidence and remains out of scope unless a later, measured need proves otherwise.

## BLOCKER RESOLUTION ROUND 2 — PHASE 5 ENTRY REVIEW (2026-09-29)

This is the latest gate assessment and supersedes earlier “focused tests not run” statements. **Phase 5 remains NO-GO.** The accepted protected baseline is **193 modules / 977 passed**, canonical command unchanged and completed outside the sandbox in 64.81 seconds. It was not rerun in this round. Focused quality/workflow/worker/database-adjacent tests passed **114 in 10.02 seconds**; exact command is recorded in `BLOCKER_RESOLUTION_REPORT.md`. No source, tests, migrations, runtime configuration, schemas or dependencies were changed.

Status meanings: **RESOLVED** means the present behavior/owner is bounded by repository evidence, not that a migration is authorized; **PARTIALLY RESOLVED** means some runtime facts are established but parity/consumer/policy evidence is incomplete; **UNRESOLVED** means a decision or critical evidence is missing; **NOT APPLICABLE** is used only where the concern does not apply.

| Blocker | Status | Exact evidence | Affected components and risk | Required decision / migration consequence |
|---|---|---|---|---|
| Protected baseline and prior sandbox error classification | RESOLVED | Canonical outside-sandbox run 193 modules / 977 passed in 64.81s; prior 103 `tmp_path` errors reproduced as sandbox `PermissionError: [WinError 5]`, while the minimal test passed outside sandbox. Current focused set 114 passed. | Test environment only; do not treat sandbox run as source regression. | Keep baseline unchanged and rerun in an authorized writable context before any future slice. |
| Quality owner and runtime topology | RESOLVED | `/validate` → `QualityService` → planner/capability executor → clean/validate/QA; DataHealth is separate. Registry/plugin/rule/validator call sites inspected. | API, application quality, capability executor, validators/plugins, reports, traces, DataHealth. | Preserve current evidenced owners; no physical move follows from ownership alone. |
| Quality semantics across API/workflow/capability/worker/categories | PARTIALLY RESOLVED | Direct API, capability, workflow and category flows traced; 114 focused tests pass. Real workflow chain test covers clean+validate, not full QA/report. Worker tests use fakes. Direct API and workflow differ in reports, traces, validation logs and persistence. | Quality API, `QualityService`, capabilities, `WorkflowEngine`, worker, validators, `ReportAgent`, DataHealth. Risk of changed errors, cache IDs, issue ordering, report/trace loss. | Define intended contracts and pass path/category parity tests before a unifying migration. |
| DataHealth linkage | UNRESOLVED | Upload route does not pass `dataset_id`; DataHealth reads completed dataset-linked direct executions/logs; workflow has separate execution record/repository. | Quality upload, workflow execution, dataset persistence, DataHealth/Copilot diagnostics. Risk of diagnostics omitting recent validation/workflow results. | Data/product owner must decide expected linkage; add evidence/test before changing ownership or persistence. |
| Sync/worker workflow shared engine path | PARTIALLY RESOLVED | Full production wiring uses same pinned workflow version/plan and `execute_existing`; runtime applies auth/compliance/quota/risk gates before both. Worker does not repeat them; async delivery differs; test worker is fake. | Runtime service, engine, worker, queue, policy collaborators and public API. Risk is stale authorization/policy, response/report behavior divergence. | Decide delayed execution gate semantics; characterize fallback and real-quality worker path before migration. |
| Worker crash/recovery | UNRESOLVED | Claim changes QUEUED→RUNNING before process work; Redis XAUTOCLAIM recovers transport only. On redelivery, queued-only DB claim yields no work, worker returns normally and consumer ACKs. No lease, heartbeat, stale detector, reconciliation or retry found. | Worker, DB state/repository, Redis queue/consumer, engine persistence. Risk of indefinitely stuck/lost work and unsafe partial replay. | Define idempotent recovery/retry and partial-side-effect policy; prove with process-death-window test. No worker/queue migration before then. |
| DB `create_all`/Alembic authority and bootstrap | UNRESOLVED | `make_session_factory` unconditionally calls create_all; `Container` makes it reachable from production API and worker. Empty SQLite→Alembic failed `NoSuchTableError: datasets` at d14; create_all (31 tables)→Alembic failed SQLite `CircularDependencyError` at 7757. No `datasets` create migration, Alembic upgrade test, predecessor upgrade test or restore rehearsal found. | API/worker startup, metadata, Alembic history, deploy/runbook and operator recovery. Critical risk: fresh bootstrap failure or modifying unexpected deployed state. | Decide authority, supported DBs and start states; prove fresh/upgrade/partial, schema equivalence, API/worker startup and backup/restore. No schema/startup change until passing. |
| Compatibility/public/external surfaces | PARTIALLY RESOLVED | API/OpenAPI, root dashboard and worker launchers active/documented; plugin subtree discovery active; README documents import shims; empty `ai/controllers/views` have no internal consumers. Repository cannot establish absent external consumers; provider live behavior untested. | API clients, operators, plugin authors, provider users, external importers. Risk of breaking undocumented integrations. | Preserve shims/launchers; resolve external compatibility and provider contract for each proposed slice. No deletion/deprecation inferred. |
| scikit-learn ownership/use | RESOLVED (ownership); PARTIALLY RESOLVED (behavior contract) | One direct import: `domain/quality/anomalies.py` IsolationForest called by QAAgent; affects anomaly rows/quarantine and report count. | Quality capability and any workflow serialization. | Keep in quality for now; exact supported-version anomaly indices, score/quarantine/report and persistence parity must be tested before relocation. |
| Physical target paths / `src/platform` | RESOLVED | Current imports/consumers do not justify a broad `src/platform` move; targets remain proposals. | All proposed modules and external import paths. | Prove a bounded target per slice; do not create structural target for consistency alone. |
| Rollback/recovery adequacy | UNRESOLVED for critical runtime/schema slices | Generic file revert is possible, but worker replay/idempotency and DB restore are not tested; fresh DB paths fail. | Worker state/output, database and public contracts. | Require actionable tested rollback/recovery specific to each chosen slice, including restore rehearsal for any schema effect. |
| Phase 5 readiness | UNRESOLVED — **NO-GO** | Worker failure recovery and DB lifecycle are critical blockers; quality parity, DataHealth linkage, compatibility and sklearn contracts are partial/unknown. | Any structural migration could lose behavior, strand jobs or affect data/startup. | Do not start Phase 5. Satisfy all exact entry conditions below first. |

### Exact Phase 5 entry conditions

Phase 5 can be reassessed only when all are met with repository/runtime evidence:

1. Reconfirm the unchanged canonical baseline: **193 modules / 977 passed**, with exact command and warnings/errors recorded, immediately before the first future slice.
2. Establish intended quality contracts and passing parity evidence for direct API, direct capability, sync workflow, real worker execution, plugin and fallback validators, all active categories, cache behavior, errors, ordering/autofix, reports, traces, persistence and the decided DataHealth linkage.
3. Decide and test sync/worker policy timing, terminal states, duplicate delivery, retry semantics and crash-after-claim recovery. No stale RUNNING execution may be left without an explicit, tested operator/runtime recovery route.
4. Approve database lifecycle policy and supported state matrix; pass fresh bootstrap, upgrade from every supported predecessor, partial-state behavior, create_all/Alembic policy, schema equivalence, API startup, worker startup, and backup/restore/recovery tests for each supported engine.
5. Bound external compatibility/provider consumers for selected surfaces or retain import/launch shims with a tested compatibility contract. Do not mark unknown consumers dead.
6. Pin pandas/sklearn DataFrame inputs, supported-version anomaly outputs, quarantined rows, score, reports and persistence/serialization behavior.
7. For every proposed path change, show current consumers, exactly one canonical owner, evidence for the proposed target, passing validation gates, acceptable risk and tested rollback/recovery. Targets remain proposals until that evidence exists; no `src/platform` move is presumed.
8. Complete the approved Phase 0–4 evidence work and keep destructive database changes out of early phases. Passing a test suite alone does not satisfy this gate.

**Recommended first migration slice: none is ready.** Once every entry criterion passes, reassess the smallest isolated, non-schema slice with fully bounded consumers and rollback. The previously proposed memory-service slice is still only a candidate and must be revalidated at that time. No Phase 5 work has started or been authorized by this evidence update.

## PHASE 4.5 — UPDATED PHASE 5 ENTRY REVIEW (2026-09-29)

This is the latest review after runtime correctness work. **Phase 5 remains NO-GO.** No package reorganization or architecture migration occurred. The canonical test collection remains 193 modules / 977 tests.

| Blocker | Status | Evidence before | Change and regression coverage | Evidence after | Remaining risk / gate consequence |
|---|---|---|---|---|---|
| Execution crash after claim | RESOLVED for Redis pending delivery | Worker crash after QUEUED→RUNNING led redelivered queued-only claim to no-op and ACK, stranding RUNNING. Terminal writes could race/overwrite. | Pending Redis message lease is renewed while owned; recovered delivery conditionally persists FAILED and uses existing state transition telemetry. No automatic replay. Terminal writes now use nonterminal conditional updates. Existing async-state, Redis queue and worker entrypoint tests reproduce crash window, duplicate recovery, lease renewal and wiring. | Recovery persists one FAILED terminal state; duplicate recovery and late completion cannot replace it. Covered tests pass in focused/full runs. | A lease expiry during process pause/network issue can fail active work; already-issued external side effects cannot be rolled back. No auto retry. Operationally accept the at-most-once/manual-resubmit policy before worker/queue migration. |
| Fresh test/development DB | RESOLVED for test/development | `create_all` generated 31 tables but its intended scope was unclear. | Kept metadata creation in nonproduction; existing persistence test proves fresh tables and first repository query. | Pass. | This is not Alembic upgrade; do not treat as production provisioning. |
| Alembic-managed API/worker startup | PARTIALLY RESOLVED | API and worker Container construction unconditionally called `create_all`. | Production Container skips metadata creation and requires current Alembic head. Existing persistence test builds a current-head schema and verifies API+worker startup policy without schema mutation. | Pass on test-stamped current-head SQLite schema. | Real production PostgreSQL/database startup and operator schema equivalence are unverified. |
| Empty Alembic bootstrap | UNRESOLVED | Empty SQLite `alembic upgrade head` fails at d14 with `NoSuchTableError: datasets`; no revision creates datasets. `create_all` then Alembic fails at 7757 with SQLite `CircularDependencyError` because current metadata is later than that additive revision's expected workspace schema. | No historical Alembic edits. The runtime now refuses unversioned production DB startup. Regression test verifies failure is fail-fast and non-mutating. | Failure is bounded and not misclassified as app/test regression; no fresh Alembic success is claimed. | There is no supported fresh production Alembic bootstrap. Must establish an approved initial-schema/provisioning path and test it before Phase 5. |
| Existing DB upgrade | PARTIALLY RESOLVED | Actual supported starting revision unknown. | Existing persistence test runs data-bearing `alembic upgrade head` from `20260926_01` to `20260928_01`, asserting ChangeSet hash backfill. | Latest predecessor edge passes on SQLite. | Earlier revisions, other DB engines, deployed starting state and backup/restore remain untested. Phase 5 stays NO-GO pending supported-state coverage. |
| Representative quality sync/worker parity | RESOLVED for one streaming workflow | Real worker quality execution, result/trace and failure parity were unproven. | Existing real capability-chain test now runs actual clean+validate capabilities and Fashion rules through inline and worker streaming paths over same DataFrame source; compares trace input/output, state, persisted outputs, error/status/trace. | Matching success result/trace; same unsupported category yields same failure. Workflow does not create direct QualityService report records, by design. Focused suite passes 124; full suite passes 977. | Does not prove direct upload/API reports/cache, every validator category, or every workflow serializer. Overall quality parity remains PARTIAL. |
| Protected baseline | RESOLVED / RECONFIRMED | Accepted 193 modules / 977 passed; preserved as fixed baseline. | Assertions were integrated in existing tests; no new test module/case count. | Focused suite **124 passed in 14.05s**; canonical unchanged command **977 passed in 66.12s**; collection **193 modules / 977 tests**. | Run in process context with writable pytest temp/cache. |

### Exact remaining Phase 5 conditions

Phase 5 must remain **NO-GO** until:

1. A safe fresh production provisioning path is evidenced. The existing empty SQLite Alembic path is known to fail; a test/dev `create_all` run does not satisfy this condition.
2. Supported existing schema predecessors and production database engines are listed and pass upgrade tests, including API/worker startup, schema equivalence and backup/restore. The only newly proven upgrade is SQLite `20260926_01→20260928_01`.
3. The Redis recovery policy's lease expiry, process pauses, Redis failure, duplicate delivery and manual resubmission consequences are operationally accepted; no hidden retry assumption remains.
4. Broader quality parity is proven wherever a migration would unify behavior: direct API/report/cache, all active category validators, workflow/worker execution and persistence. The tested streaming workflow is only representative evidence.
5. Exact migration slice, current consumers, canonical owner, proposed target, validation and rollback/recovery remain evidence-backed; all proposed paths stay proposals. No `src/platform` move is presumed.
6. The unchanged **193-module / 977-pass** canonical suite is rerun immediately before a later Phase 5 slice and remains green.

**Recommended first migration slice: none.** The production database bootstrap/lifecycle blocker is sufficient to keep Phase 5 NO-GO. Reassess only after the exact conditions above pass. No Phase 5 migration started.
## PHASE 5 ENTRY REVIEW — PHASE 4.6 (2026-09-29)

**PHASE 5: NO-GO.** This pass made documentation-only updates. No source, test, migration, schema, dependency, or runtime configuration changed. The canonical baseline is unchanged and currently verified at **193 modules / 977 passed**.

### Blocker statuses

| Concern | Status | Repository evidence | Risk / required correction |
|---|---|---|---|
| Empty Alembic bootstrap | **BLOCKED — EVIDENCE REQUIRED** | Exact empty SQLite CLI run fails in `d14c1f2a9b31_add_dataset_storage_key.py:22` on inspector `get_columns("datasets")`; no ancestor creates that table. Later revisions also assume `datasets` and `workflow_executions`. API startup is not reached. | Establish the authoritative prior schema/clean-install provisioning contract; validate it with Alembic and application/worker startup on the supported production DB. Do not guess, stamp, or use production `create_all`. Blocks Phase 5. |
| Existing database migration lifecycle | **PARTIALLY RESOLVED** | Current-head startup policy and one metadata-prepared SQLite `20260926_01→20260928_01` data-bearing upgrade test. | Earlier/deployed start states, supported production engine, backup/restore remain unproven. |
| API report vs workflow report | **RESOLVED as distinct contracts** | Direct API `/validate` runs QualityService, capability plan, trace/context persistence, report generation and execution-specific report URL mapping. Workflow/worker persists workflow outputs/traces and has no report path/API contract. Existing API test exercises a real capability pipeline. | Preserve the API report contract; no evidence requires worker to generate direct API reports. NOT A PHASE 5 BLOCKER. |
| Cache cross-runtime parity | **RESOLVED as non-shared contract; PARTIALLY RESOLVED behavior** | `QualityService` consumes application Cache protocol; `TTLCache` is infrastructure implementation. Key includes upload bytes, resolved category, rule version; TTL uses monotonic time; no explicit invalidation. Workflow/worker does not consume this cache. Lookup occurs after execution, trace/context persistence and COMPLETED state, then a hit returns the previous summary and skips saving the new result. | Absence of worker cache is not an architectural violation. Decide whether a cached API attempt must have its own result/report persistence before any cache-specific migration. The current completed-row-without-own-result behavior is a contained application correctness/observability risk. |
| Validator categories through worker | **PARTIALLY RESOLVED** | Registry yields Cosmetics, Fashion, HomeAppliances, plugin-first. Shared ValidationCapability and ValidatorAgent contract dispatch all categories. Fashion has real inline/worker parity evidence; category implementations and registry are locally tested. | Cosmetics and HomeAppliances worker end-to-end behavior is untested. Their implementation differences are category-specific, not evidence of a broken boundary. Do not change these behaviors in a slice without category-specific worker tests. |
| Worker recovery | **RESOLVED within tested Redis scope** | Phase 4.5 regression proves recoverable claimed execution reaches conditional FAILED and duplicate recovery/late terminal write cannot replace terminal state. | Lease-expiry/side-effect limitations remain documented; no new blocker introduced. |
| Representative sync/worker operation | **RESOLVED within selected workflow** | Real streaming `data.clean → data.validate` path compared inline and worker for dispatch, output, traces, state and invalid category behavior. | Scope is that representative workflow only; no universal parity claimed. |
| Protected test baseline | **RESOLVED** | Focused normal-context suite: 31 passed in 8.01s. Unchanged canonical command: 977 passed in 68.97s; 193 modules. Sandbox-only temp errors are the previously confirmed environment restriction. | Baseline remains protected; use a test context with writable pytest temp/cache locations. |

### Final gate

Phase 5 remains **NO-GO** because a clean database cannot currently reach Alembic head from the checked-in migration history on the tested engine, and production-engine behavior is not proven. No architecture migration or database-history repair is safe until the missing historic schema prerequisite is evidenced and an approved clean-install contract is established. API/workflow report differences are intentional use-case distinctions; lack of worker cache is not a parity requirement; validator implementation differences are category-specific, with uncovered category worker behavior explicitly bounded.

#### Exact Phase 5 entry conditions

1. Establish and document the authoritative clean-install/pre-Alembic schema contract without production `create_all`, migration bypass, stamping, or fabricated SQLite equivalence.
2. Prove on the supported production database engine: empty supported database → schema provisioning/Alembic head → API and worker startup → first repository operation. If production bootstrap intentionally requires pre-provisioned schema, document who creates it, the exact versioned artifact/process, and test that process end to end.
3. Test supported existing upgrade edges, schema compatibility at head, backup/restore and rollback/recovery assumptions.
4. Preserve worker crash recovery and the selected sync/worker quality contract; define operational lease/side-effect retry policy before worker changes.
5. Keep API reports as an application use-case contract. Decide whether cache-hit API attempts require own persisted result/report associations before any cache-specific migration.
6. If a migration slice changes validation dispatch or worker behavior, add worker E2E cases for Cosmetics and HomeAppliances while retaining the shared capability contract and Fashion plugin/legacy import compatibility.
7. Reconfirm the unchanged **193 modules / 977 passed** canonical suite immediately before any later, separately authorized Phase 5 work. Record slice-specific consumers, validation, and rollback.

**Recommended first migration slice: none.** The clean database lifecycle is a hard blocker; resolve it and verify the supported production-engine bootstrap before proposing a first slice.

## MIGRATION_HISTORY_STATUS — PHASE 4.7 FORENSICS (2026-09-29)

**Phase 5 remains NO-GO. No migration repair was attempted.**

- **MIGRATION_HISTORY_STATUS:** Alembic has 23 connected revisions and one head `20260928_01`. The first migration referencing `datasets` is `d14c1f2a9b31`; no earlier revision creates that table. Empty SQLite `upgrade head` fails at that revision. A separate static graph issue exists: `7757af5afe0a` and later `fcbc1a52044c` both create `workspaces` (first conditionally, later unconditionally), so the baseline/start-state contract must be checked against the entire chain.
- **AUTHORITATIVE_SCHEMA_SOURCE:** historical Git commit `192a9ea` added Alembic as a patch to an existing persistence schema and still called `Base.metadata.create_all()` during container construction. Git commit `977fb44` adds `DatasetRecord` and updates the tracked local DB; `9a7a57a` adds the storage-key alter migration without creating the table. Historical ORM startup is the likely pre-provision mechanism. It is not a versioned historical DDL source and does not prove production used it. Local tracked `data_quality.db` is a current historical artifact, not production authority.
- **PRODUCTION_SCHEMA_STATUS:** **PRODUCTION SCHEMA STATE = UNVERIFIED.** PostgreSQL 16 is specified in production Compose/operator docs, but no production connection, dump, deployment log, backup, or operator baseline record is available. No secrets were read or reported.
- **MIGRATION_REPAIR_REQUIRED:** a clean supported path is required because current production startup is Alembic-first and disables `create_all`; whether this needs a recovered historical baseline migration, explicit external provisioning, or another process cannot be determined yet. Do not change history until the schema source is authoritative.
- **MIGRATION_REPAIR_CONFIDENCE:** high confidence in missing-from-empty behavior; medium-high confidence historical migrations assume pre-provisioning; low confidence in which repair is correct.
- **Migration model:** **B — Alembic starts from a pre-provisioned baseline schema**, high confidence for historical repository intent. The actual baseline and production use are unverified. No evidence of deleted/squashed revisions or multiple current heads exists in reachable `main`; all-ref history completeness is limited by a broken local checkpoint ref.

The exhaustive chronological revision effects and source classification are recorded in `BLOCKER_RESOLUTION_REPORT.md` in its Phase 4.7 section. Required next evidence is the historical/deployed PostgreSQL baseline schema and provisioning/deployment record. Phase 5 entry remains blocked until a safe, versioned bootstrap is proven on PostgreSQL 16. No code, test, migration, schema, dependency, or startup behavior changed in this pass.

## PHASE 4.8 — PRODUCTION BASELINE STATUS

- **PRODUCTION_DB_ENGINE:** PostgreSQL.
- **PRODUCTION_DB_VERSION:** 16 is the repository target; actual production runtime version is unverified.
- **PRODUCTION_SCHEMA_PROVISIONING_METHOD:** production method unknown. Historical application `create_all()` is plausible, but no production deployment evidence proves it was used. No SQL/init script, migration service, or external baseline artifact is checked in.
- **PRODUCTION_MIGRATION_METHOD:** operator runbook specifies `alembic upgrade head`; production Compose does not run it. Deployment guide says `up -d`. These steps are potentially complementary but lack a documented executable order, so classify the deployment instructions as incomplete.
- **PRODUCTION_STARTUP_ORDER:** PostgreSQL and Redis health gates precede API/worker/dashboard; Nginx waits on API health and dashboard. No schema migration occurs in Compose; API and worker require the current Alembic head.
- **PRODUCTION_SCHEMA_BASELINE:** INSUFFICIENT. Local tracked SQLite `data_quality.db` at head is not a PostgreSQL production artifact.
- **PRODUCTION_SCHEMA_BASELINE_CONFIDENCE:** LOW for any production schema assertion.
- **POSTGRESQL_RUNTIME_VERIFICATION:** UNAVAILABLE. Docker and PostgreSQL client/readiness tools were unavailable; no authorized isolated PostgreSQL 16 service was identified. SQLite was not used as a substitute.
- **ALEMBIC_TAKEOVER_STATUS:** NO for an empty PostgreSQL DB; UNKNOWN for the existing production baseline and general future upgrades.
- **MIGRATION_REPAIR_STATUS:** BLOCKED pending authoritative baseline/provisioning evidence.
- **PHASE_5_GATE:** NO-GO.

Historical provisioning evidence and A–F source classifications, exact deployment-flow analysis, artifact search, and takeover matrix are in `BLOCKER_RESOLUTION_REPORT.md` under **PHASE 4.8**. The historical `create_all()` caller proves a code path existed, not that production used it. No migrations or other implementation files were changed.

## PHASE 4.9 — EXTERNAL EVIDENCE GATE

Repository-only investigation is closed. The next step requires an authoritative production-equivalent artifact: isolated PostgreSQL 16 staging database, schema-only PostgreSQL dump, approved production schema snapshot, authoritative provisioning artifact, or equivalent deployment database artifact. Record database version, capture date, deployment version, and baseline revision if known. Do not infer the baseline from ORM models or SQLite.

When supplied, verify: (A) empty PostgreSQL provisioning, (B) authoritative existing schema, (C) Alembic upgrade from that schema, (D) API startup, (E) worker startup, (F) representative database operation, and (G) backup/restore assumptions where evidence exists.

Record explicit answers to: what creates the initial schema; when Alembic becomes authoritative; what revision represents the baseline; whether Alembic upgrades the existing production baseline; whether a new environment reproduces it; and the supported provisioning/migration/API/worker order.

- **PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
- **POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
- **MIGRATION_REPAIR = BLOCKED**
- **PHASE_5 = NO-GO**

Do not proceed to migration repair until this gate is satisfied. No implementation or database files were changed.

## EXTERNAL EVIDENCE ACQUISITION — ENVIRONMENT CHECK

Docker/Compose, PostgreSQL client/server commands, PostgreSQL processes, and PostgreSQL Windows services are unavailable. The repo defines PostgreSQL 16 in Compose, but CI has no PostgreSQL service and development defaults to SQLite. No staging database is configured or available. No database connection was attempted; SQLite was not substituted.

- **POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
- **BACKUP_RESTORE_VERIFICATION = UNAVAILABLE**
- **EMPTY_DATABASE_ALEMBIC_BOOTSTRAP = UNKNOWN (not run on PostgreSQL)**
- **EXISTING_BASELINE_ALEMBIC_UPGRADE = UNKNOWN**
- **API_STARTUP = UNKNOWN on PostgreSQL**
- **WORKER_STARTUP = UNKNOWN on PostgreSQL**
- **PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
- **ALEMBIC_TAKEOVER = UNKNOWN for existing baseline**
- **MIGRATION_REPAIR = BLOCKED**
- **PHASE_5 = NO-GO**

External request: provide one of (A) PostgreSQL 16 schema-only dump from the authoritative environment, (B) isolated PostgreSQL 16 staging database representing production baseline, or (C) authoritative schema provisioning artifact. Include only PostgreSQL version, baseline date/revision, provisioning method, required extensions, migration state, and environment type (production/staging/development). Credentials and secrets are not required. After receipt, verify only in an isolated disposable PostgreSQL 16 database; never connect to production or alter shared databases.

## PHASE 5 PREFLIGHT — APPLICATION MEMORY BOUNDARY (DESIGN ONLY)

**SLICE = APPLICATION MEMORY PERSISTENCE PORT**; **SLICE_STATUS = READY** for the bounded dependency-inversion design in `MIGRATION_PLAN.md`. This is not authorization: **PHASE_5 = NO-GO** and **SLICE_EXECUTION = NOT_AUTHORIZED**.

Evidence: `application/memory/memory_service.py` directly imports and annotates `repositories.agent_memory.AgentMemoryRepository`, a confirmed application→repository boundary violation. The adapter maps SQLAlchemy `AgentMemoryRecord` and implements tenant-filtered persistence, expiry filtering/eviction, ordering, and commits. Existing revision `c13a7e91d204` creates `agent_memory` and assumes `workspaces`/`users`. The domain types are in `domain/agent_memory.py`; `domain/memory.py` is a compatibility re-export. `services/container.py` wires adapter→use case→`ParameterResolver` and `AutonomousOperationsOrchestrator`.

Consumer evidence bounds the claim: Copilot workflow authoring reaches the requirement agent with `workspace_id=None`, so the resolver’s current tenant guard prevents a memory query. No direct API memory endpoint or route to the autonomous orchestrator was found. The worker builds the shared container but the inspected workflow worker does not call memory. Tests cover use-case redaction/mapping/scoping, SQL adapter roundtrip/tenant isolation/expiry, integrated correction-aware requirement resolution, resolver optionality, and optional autonomous learning. SQLite `create_all()` in the repository/integration tests proves test adapter behavior only, not PostgreSQL production schema compatibility.

The proposed slice preserves model/table/migration, SQL/query/transaction behavior, session factory, startup, and existing import/constructor contracts. It proposes an application-owned repository protocol, canonical adapter module under existing `infrastructure/persistence/`, `repositories.agent_memory` re-export, service typing to the port, and one composition-root import change. It needs no migration, schema change/repair, or production database access. The production runtime’s existing table requirement remains unresolved and must not be misrepresented as verified. No architecture-wide move is proposed.

Rollback is a single isolated source-patch revert, restoring the prior container import and retaining the legacy import path; no data rollback is involved. Named tests, proposed future commands, in-scope/out-of-scope files, and migration order are in `MIGRATION_PLAN.md`. No tests were run in this preflight.

**Gate remains:** `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`; `POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE`; `BACKUP_RESTORE_VERIFICATION = UNAVAILABLE`; `MIGRATION_REPAIR = BLOCKED`; `PHASE_5 = NO-GO`; `SLICE_EXECUTION = NOT_AUTHORIZED`.

### Implementation-readiness review correction (2026-10-02)

The slice is **IMPLEMENTATION_READY_WITH_WARNINGS**, not unconditionally ready. The code-level contract and boundary are bounded, but existing tests do not explicitly prove the old import is the same class as the canonical infrastructure adapter or that the application container wires the canonical implementation. The mandatory minimum tests and exact three-method port signature/transaction/error semantics are now recorded in `MIGRATION_PLAN.md`.

Current composition evidence: API startup builds `Container` in `api/main.py`; worker startup calls `build_container` in `worker.py`; both converge on the one adapter construction in `services/container.py`. Dashboard code has no direct memory/repository references. Non-test source consumers of `repositories.agent_memory` are the memory application service and composition root; the application use case must stop importing the compatibility facade, while the composition root must import the canonical infrastructure module. Tests remain current compatibility consumers. No direct concrete-repository dependency exists in the agent consumers.

The current worktree already modifies `services/container.py` to pass `create_schema` and `require_current_revision` into `make_session_factory`. That unrelated database-startup change must be preserved verbatim; the proposed memory slice should touch only its repository import in that file. This increases patch-integration care but does not require changing the slice boundary.

No protocol/adapter cycle is required: protocol is application-owned; adapter imports domain and database models and may depend inward on the protocol; legacy facade imports/re-exports the adapter; application must never import the facade. The change remains behavior-preserving only if `create`/eviction commit boundaries, per-call session ownership, query scope/order/expiry semantics, and unwrapped persistence errors remain unchanged. No code or tests were modified or run. Global Phase 5 gate remains NO-GO and slice execution remains unauthorized.

## NEXT SLICE SELECTION — POST-MEMORY REVIEW (2026-10-02)

After the completed memory persistence port, the next highest-readiness candidate is the single owner-scoped sync-job status API read. Repository evidence: `api/routes/channels.py` currently injects `SyncJobRepository` for `GET /sync-jobs/{sync_job_id}` and maps a missing/foreign-owner result to 404; `repositories.sync_jobs.get_for_owner` already performs workspace-owner filtering. `ChannelSyncService` already owns and receives that same `SyncJobRepository`, and `api.dependencies.get_channel_sync_service` already exposes it to the route. Existing `tests/test_api_channels.py` verifies owner-scoped success, missing/other-owner 404, and public response behavior; `tests/test_channel_sync_service.py` has repository fakes; `tests/test_sync_job_repository.py` covers persistence scoping.

**Selected slice:** delegate this GET lookup through `ChannelSyncService`, keep response mapping and authorization unchanged, and retain `get_sync_job_repository` as compatibility-only. Exact file/test plan and rollback are recorded in `MIGRATION_PLAN.md` under “NEXT SLICE SELECTION”. This removes the active route-to-repository call, but does not remove the retained compatibility provider or the repository's use within the application service.

Other reviewed tensions were not selected: application→services edges are shared policy services; remaining application→repository operations include transaction/session contracts; execution-history endpoints span two repositories, reports and aliases; channel listing adds a separate workspace authorization check; quality/capability legacy paths still require parity evidence; validators have active fallback/category contracts; physical repository/model/schema moves are broader and database-blocked; `models.*`/`api.schemas` are compatibility surfaces; workflow/execution has state/parity requirements; and the legacy `ai/` package lacks proven active ownership. See the migration plan for readiness-ranked viable channel read candidates and the detailed selected-slice record.

**Status:** `READY_WITH_WARNINGS` as preflight only. The retained API dependency getter is a transitional bypass that this single-route slice does not remove. `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`; `PHASE_5 = NO-GO`. This preflight changed documentation only; source and tests were not changed and no tests were run.
# Final architecture audit — closure status (2026-10-02)

The post-slice final audit is documented in `ARCHITECTURE_CLOSURE_REVIEW.md`. The three completed bounded slices are the Application Memory Persistence Port, owner-scoped sync-job status route, and ChangeSet Query Persistence Port. The audit found no further candidate that meets the current readiness constraints without inferring an owner or risking behavior/compatibility. Consolidation is therefore **closed with documented debt**, not globally complete.

Current status: `NEXT_CANDIDATE=NO_SAFE_NEXT_SLICE`; `PREFLIGHT=NOT_READY_FOR_PREFLIGHT`; `NEXT_SLICE_EXECUTION=NOT_AUTHORIZED`. The remaining direct application-to-repository consumer census, route/service/capability edges, workflow/execution boundaries, compatibility surface, classification register, and reopening conditions are in the closure review.

The canonical unchanged suite reported **992 passed / 195 modules** both before and after the audit-document edits (final run: 67.63 seconds); `git diff --check` passed. The change from 977 tests is attributable to 15 regression tests across the three authorized completed slices. No source, tests, database migrations, schemas, runtime configuration, startup, API or worker behavior changed in this review.

Database status is unchanged and remains a separate blocker: `PRODUCTION_SCHEMA_BASELINE=UNKNOWN`; `POSTGRESQL_RUNTIME_VERIFICATION=UNAVAILABLE`; `BACKUP_RESTORE_VERIFICATION=UNAVAILABLE`; `MIGRATION_REPAIR=BLOCKED`; `PHASE_5=NO-GO`. Phase 5 requires the external production-equivalent PostgreSQL evidence and verification specified in the closure review; architectural closure does not satisfy that gate.

## Final migration repair and validation status — 2026-10-02

The preceding architecture and discovery entries are historical snapshots; this final gate records the later Strategy D repair and validation. The active Alembic graph is single-base/single-head `20261002_01`, with 23 former revisions archived and inactive. Fresh install and representative PostgreSQL 16.15 persistence Groups 1–7 passed; observed schema counts were 31 application tables, 43 foreign keys (all `NO ACTION`), 67 explicit/application indexes, and 109 total indexes. Fresh seed policy passed without demo, admin, or application seed rows.

The canonical command `.\venv\Scripts\python.exe -m pytest -q` completed with **994 collected / 994 passed**, 0 failed, errors, skipped, or warnings, in **75.14 seconds**. `tests/test_persistence.py` now derives the configured current head and tests the active clean-install path rather than the archived historical upgrade edge. The production revision guard was preserved. `git diff --check` passed.

The project has never had a production/staging database or production data. The disposable local database is not production-equivalent; production schema/revision status, backup/restore evidence, production-equivalent upgrade rehearsal, and deployment/provisioning order remain unresolved. Architecture consolidation remains closed with documented debt, with no safe next architectural slice.

```text
MIGRATION_REPAIR_VALIDATION = PASS
POSTGRESQL_PERSISTENCE_VALIDATION = PASS_WITH_REPRESENTATIVE_COVERAGE
FULL_REGRESSION = PASS
ARCHITECTURE_CONSOLIDATION = CLOSED_WITH_DOCUMENTED_DEBT
NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
DEPLOYMENT_PROVISIONING_ORDER = INCOMPLETELY_EVIDENCED
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
```
