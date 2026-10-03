# Final Architecture Audit — Consolidation Closure Review

**Audit date:** 2026-10-02  
**Scope:** repository evidence and current imports after the completed Memory Persistence Port, owner-scoped sync-job status route, and ChangeSet Query Persistence Port slices. This is a documentation-only audit. No source, tests, database migrations, schemas, runtime configuration, startup, API or worker behavior was changed by this review.

## Decision

**ARCHITECTURE_CONSOLIDATION_CLOSED_WITH_DOCUMENTED_DEBT**

The three bounded slices listed below are complete. The current audit found no further slice meeting the user's safety/readiness criteria. This closes the presently justified consolidation work; it does not claim that every boundary is clean, authorize another slice, or satisfy the production database gate.

```text
NEXT_CANDIDATE = NO_SAFE_NEXT_SLICE
PREFLIGHT = NOT_READY_FOR_PREFLIGHT
NEXT_SLICE_EXECUTION = NOT_AUTHORIZED
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
MIGRATION_REPAIR_VALIDATION = PASS (local/disposable PostgreSQL 16)
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
```

## Evidence and protected baseline

- At audit start, the canonical unchanged command `.\venv\Scripts\python.exe -m pytest -q` completed with **992 passed in 67.35 seconds**. This is 195 test modules; the 15-test increase from the earlier 977/193 baseline is attributable to regression coverage added with the three completed slices (two memory, two sync-job route, eleven ChangeSet query slice tests, per the repository's slice evidence). No warnings, failures, errors, or skips were reported by this run.
- After the completed audit-document edits, the same canonical command completed with **992 passed in 67.63 seconds**. No failures, errors, skips, or warnings were reported.
- `git diff --check` after the documentation edits returned exit code 0.
- The suite and tests were not modified for this audit.
- The initial worktree already contained source/test modifications and discovery artifacts from the authorized earlier slices. Those existing changes were preserved. This review changed only this file, `MIGRATION_PLAN.md`, and `DISCOVERY_REVIEW.md`.

## Completed consolidation slices

| Slice | Current canonical boundary | Evidence | Preserved compatibility |
|---|---|---|---|
| Application Memory Persistence Port | `application.memory.MemoryService` depends on `application.memory.ports.AgentMemoryPersistencePort`; SQLAlchemy implementation is `infrastructure.persistence.agent_memory_repository`; `repositories.agent_memory` remains a re-export facade. | Adapter/repository, service, tenant-isolation, and `tests/test_agent_memory_container_wiring.py` coverage; container wiring inspected. | Old repository import remains. Memory semantics, table, schema, API and worker behavior unchanged. |
| Owner-scoped sync-job status route | Route calls `ChannelSyncService.get_sync_job`; service performs owner-scoped lookup. | `tests/test_api_channels.py` covers owner result, foreign/missing 404, response error without credentials, and legacy provider callable; service/repository tests also cover owner scope. | Repository provider retained; route response and access behavior unchanged. |
| ChangeSet query persistence port | `application.changesets.ChangeSetQueryService` depends on its application port; existing `ChangeSetRepository` implementation and container composition remain. | `tests/test_changeset_query_service.py`, `tests/test_changeset_repository.py`, and `tests/test_changeset_api.py`; full suite. | Repository path and API contract unchanged. |

These reduce specific coupling edges; none changes the database takeover status or proves global architectural completion.

## Canonical architecture and ownership statements

These are logical contract owners based on code and current call sites, not claims that every implementation is located in an ideal physical directory.

| Concern | Canonical contract / use-case owner | Runtime mechanism or adapter | Audit statement |
|---|---|---|---|
| Domain policies and values | `domain/` concepts by bounded context | Application coordinates use cases | Keep domain contract separate from execution/persistence mechanics. |
| Application memory persistence contract | `application.memory.ports.AgentMemoryPersistencePort` | SQLAlchemy adapter under `infrastructure/persistence/` | Confirmed by current imports and composition. |
| Channel sync and sync-job query | `application.channels.ChannelSyncService` | Channel/sync-job repositories, connector adapters | Listing channels is a separate, unresolved query ownership concern. |
| ChangeSet query | `application.changesets.ChangeSetQueryService` and its port | Existing ChangeSet repository | Query boundary is explicit; mutation/rollback stay separate use cases. |
| Workflow authoring | `application.workflows.WorkflowAuthoringService` | Workflow repositories | Definitions/versions are separate from execution. |
| Workflow orchestration | `application.workflows.WorkflowRuntimeService` | Queue transport or direct engine dispatch | Application owns access/policy/quota/risk/approval and dispatch decisions. |
| Workflow execution | `execution.workflow.WorkflowEngine` | Capability executor, persistence and trace mechanisms | Engine runs the persisted version/plan; it is not the workflow authoring owner. |
| Queue transport | `infrastructure.queue` adapters | Redis Streams or in-process transport | Transport conveys execution IDs; persisted execution state remains authoritative. |
| HTTP contracts and endpoints | `api.routes` plus `schemas/` contracts | FastAPI boundary | `api.schemas` and legacy route aliases are compatibility paths. |
| ORM schema declarations | `database.models` | SQLAlchemy | Model metadata is not evidence of the authoritative historical production baseline. |
| Production schema lifecycle | **Unknown** | Alembic plus external provisioning evidence required | No trusted production-equivalent PostgreSQL baseline is available. |
| Quality / validation | Split: `application.quality.QualityService` orchestrates, `domain.quality` and `domain.validation` own relevant concepts, plugin/validator modules provide category behavior, and capability execution runs workflow steps. | Legacy `services.validation_service`, `services.data_operations`, agents, rule engine and capabilities remain active in mapped paths. | No single unified runtime path has been proven; do not consolidate by directory name. |
| Risk policy | `domain.risk` contract; `application.risk.RiskService` evaluates | Container constructs service using repository-provided policy | Risk route's per-request container wiring differs from app-scoped wiring; freshness semantics unresolved. |
| Audit and lineage | `domain.audit` / `domain.lineage` contracts; application services own orchestration | Repositories persist events | Transaction and integrity behavior makes broad movement unsafe. |
| Agents and AI providers | Agent behavior in `agents/`; provider/client adapter path includes `agents/llm.py` and composition | Legacy `ai/` package and aliases | Current internal paths are visible, but external imports are not enumerable; ownership of remaining AI compatibility modules is unresolved. |
| Capabilities | `domain.capabilities` contract and `execution` dispatch; concrete capability modules implement steps | Legacy data-operation service and agent-backed categories | Preserve capability names, order, outputs, traces and provider behavior. |
| Rule engine / plugins / validators / extractors | Rule AST/evaluation in `rule_engine/`; extension contract/discovery in `plugins/`; category behavior is distributed across validators/extractors | Quality and capability callers | Current locations are active in differing ways; category/plugin contracts and fallback ordering are not one proven interchangeable system. |
| Configuration and composition | Settings/configuration modules provide configuration; `services.container` is the observed object composition root | API and worker entrypoints invoke composition | Composition ownership is evidenced and intentional; do not move for package symmetry. |

`src/platform` is not an evidenced target and is not proposed. Repository and infrastructure persistence directories remain distinct; no tree-wide relocation is justified by this audit.

## Dependency graph after the three slices

| Edge | Status | Current evidence / disposition |
|---|---|---|
| `application.memory -> repositories.agent_memory` | **Resolved** | Memory service now targets application-owned port; repository module is a compatibility facade. |
| `application.changesets.query_service -> repositories.changesets` | **Resolved** | Query service targets its port; concrete repository remains wired at composition. Mutation services continue using persistence behavior requiring separate review. |
| `api sync-job status -> repositories.sync_jobs` | **Resolved for this route** | Route uses `ChannelSyncService`; service/repository owner scoping is covered. Other channel sync persistence edges remain. |
| `api GET /channels -> repositories.channels` | **Unchanged / transitional** | Existing workspace authorization precedes owner-scoped list; no established application channel-catalog query owner is evidenced. Defer; no one-operation service. |
| `api executions -> repositories.execution / execution traces` | **Unchanged / transitional** | Legacy history/detail and filesystem report routes use `ExecutionRecord`/trace behavior; not shown equivalent to workflow-history semantics. Keep compatibility until a contract owner and parity are established. |
| `api risk -> services.container / application risk` | **Unchanged / transitional** | Risk endpoint obtains a newly built container per request; app-scoped container differs and policy is loaded from repository at construction. Policy freshness and lifecycle are not specified. |
| `api data operations -> services.data_operations` | **Unchanged / transitional** | Existing clean/extract route behavior and quality facade overlaps are not proven equivalent to quality/capability flows. |
| `application -> repositories` | **Reduced, not eliminated** | Remaining direct imports are listed below. Most combine transactions, policy checks, multiple aggregates, or public transaction behavior. No indiscriminate porting is safe. |
| `application -> services` | **Unchanged / transitional** | Authorization/compliance/quota and validation/data-operation services still have active behavior. Several are not adapters and require contract extraction plus cross-consumer tests. |
| `capabilities -> services.data_operations` | **Unchanged / transitional** | Cleaning capability reuses legacy data-operation behavior; autofix/validation/report sequence lacks proven alternate-path parity. |
| `capabilities -> agents` | **Unchanged / intentional-or-transitional** | Agent-backed extraction/validation capabilities are live execution consumers; they do not establish that agents own capability contracts. Keep dispatch semantics. |
| `repositories.channels -> application.channels.credential_cipher` | **Unchanged / confirmed direction violation** | Concrete inward import remains; cipher contract/implementation ownership and tests must be mapped before changing it. |
| `infrastructure.persistence -> application` | **Intentional port implementation** | Agent-memory SQL adapter implements an application-owned persistence protocol. Maintain the dependency direction and avoid cycles. |
| `execution -> application/domain/infrastructure` | **Mixed / intentional and transitional** | Execution consumes domain contracts and runtime/application services, with concrete persistence/telemetry mechanisms; engine is not an application use case. Preserve separation. |
| `agents -> ai` | **Unresolved compatibility boundary** | Active provider path and legacy `ai/` modules coexist; public/external consumers are unknown. No deletion or broad import rewrite. |

### Remaining direct `application -> repositories` imports

Current source imports identify these modules; method-level consumers remain attached to the described behavior. This is not an authorization to migrate them.

| Current consumer | Concrete dependency | Why not a safe next slice |
|---|---|---|
| `application.audit.audit_service` | Audit event repository locking, in-transaction reads/writes, owner listing | Hash-chain/integrity plus transaction boundaries and multiple callers; rollback/parity must cover atomicity. |
| `application.channels.channel_sync_service` | Channel, mapping, job, attempt, dataset and project repositories | Multi-aggregate orchestration, idempotency, external connector effects and job state. |
| `application.channels.canonical_product_service` | Dataset repository plus concrete storage and tabular reader | Crosses persistence, file storage and input parsing; current ownership spans a coordinated ingestion path. |
| `application.datasets.dataset_service` | Dataset, project and workspace repositories | Access, compliance, quota, ingestion, and multi-repository behavior share one use case. |
| `application.workspace.project_service` | Workspace and project repositories | Authorization-scoped create/list/get behavior with multiple consumers and ownership rules. |
| `application.lineage.lineage_tracking_service` | Lineage repository, including transaction-taking write operation | Execution capability and API consumers; caller-owned transaction semantics are part of the contract. |
| `application.workflows.authoring_service` | Project/workspace/workflow/version repositories | Version immutability, activation, owner scope, API and Copilot consumers make a mechanical port unsafe. |

The resolved memory and ChangeSet query modules are no longer in this list. Import census should be refreshed before any future slice because this report captures the audited checkout, not a permanent guarantee.

## API and compatibility surface

- `GET /channels`: workspace/project access is checked before repository retrieval; owner isolation is applied by `list_for_owner`; route owns HTTP mapping and credential-safe output. No canonical application query owner is established.
- Execution legacy routes read execution/trace repositories directly and derive report file paths. Workflow history services use workflow execution records and have different semantics. Do not redirect without response/error/report/authorization parity evidence.
- Risk evaluation route uses `get_container()` and `build_container()` per request. The app startup also creates and stores a container. The repository-loaded policy may therefore be refreshed at a different cadence. The intended freshness contract is not documented or test-proven; retain current path.
- `repositories.agent_memory`, `api.schemas`, `models.database`, `models.domain`, legacy API aliases, dashboard launch modules and provider integrations remain compatibility surfaces where internal/public consumption cannot be ruled out. Do not delete them as cleanup.
- `services.container` is an intentional outer composition root when used by API/worker startup; route-level access to the container is transitional coupling.

## Workflow and execution boundary

`WorkflowAuthoringService` owns persisted workflow definitions/versions. `WorkflowRuntimeService` owns synchronous/queued request orchestration, scope and policy gates, quota/risk/approval checks, and dispatch choice. `WorkflowEngine` loads the persisted workflow version/plan, invokes capability execution, records traces, and persists execution outcomes. Queue adapters carry execution IDs; they do not define business workflow semantics.

Sync and worker paths are related but not interchangeable at the boundary: sync returns the runtime result inline, while async returns an execution ID and the worker later persists terminal state/report/trace. Risk/approval may prevent dispatch; queued execution has delivery lease/recovery behavior. Worker recovery marks a reclaimed RUNNING execution FAILED and does not replay capability side effects, by design documented in `WorkflowExecutionWorker.recover`; conditional terminal writes guard duplicate terminal completion. Redis pending recovery uses a 60-second default idle threshold and renews the pending delivery while processing. These facts do not prove universal sync/worker quality parity or production Redis reliability; those are outside consolidation closure and remain runtime operational concerns.

## Debt register

Each item is assigned exactly one requested classification.

| ID | Classification | Evidence and affected boundary | Disposition / consequence |
|---|---|---|---|
| A1 | **E. ACTIVE ARCHITECTURAL RISK** | `repositories.channels` imports the credential cipher contract from `application.channels`. | Confirmed inward-direction violation. Leave unchanged until a neutral contract boundary and encryption behavior tests are specified. |
| A2 | **E. ACTIVE ARCHITECTURAL RISK** | API execution history/detail/report routes access repositories and execution internals directly. | Actual API bypass exists; keep behavior but require a contract before redirecting legacy and workflow history/report paths. |
| A3 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Capabilities cleaning path imports `services.data_operations`; capabilities also depend on agents in other categories. | Must define capability input/output, autofix/validation/report ordering and trace/error contracts before changing ownership. |
| B1 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | `GET /channels` uses a repository after workspace authorization; no existing application owner proves it should move. | Do not invent a service. Migration requires evidence of a broader channel-catalog use case and query contract. |
| B2 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Application modules still import repositories, including the seven modules enumerated above. | Each has transaction, multi-consumer, policy, versioning or I/O semantics; define per-use-case persistence/transaction contract before any port. |
| B3 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Routes access legacy `services.*`, and risk route accesses the container directly. | Define ownership, error/response behavior and (for risk) policy refresh/lifetime before changing wiring. |
| B4 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Quality/validation behavior is distributed across application, domain, services, capabilities, agents, validators, extractors, plugins and rule engine. | Define category contracts, discovery order, cache behavior and report/trace semantics; no whole-pipeline equivalence is established. |
| B5 | **B. TRANSITIONAL BUT SAFE** | Adapters are split between `repositories/` and `infrastructure/persistence/`; ORM compatibility aliases remain. | Current runtime works and no duplicate same-table implementation is established. Retain split/shims; a tree move is not justified. |
| B6 | **A. INTENTIONAL COMPATIBILITY** | Legacy AI/provider, dashboard/controller/view, repository, model, API schema and route surfaces may have external consumers. | Preserve paths and aliases because repository search cannot rule out external imports. |
| C1 | **A. INTENTIONAL COMPATIBILITY** | API/worker startup use `services.container` to compose application, domain and infrastructure objects. | It is the observed outer composition root, not a route/service ownership defect. Keep until replacement evidence exists. |
| C2 | **A. INTENTIONAL COMPATIBILITY** | Application memory port is implemented by infrastructure SQLAlchemy adapter; old repository path re-exports it. | The port direction is valid and facade intentionally preserves import compatibility. |
| C3 | **B. TRANSITIONAL BUT SAFE** | Workflow runtime dispatches to engine and queue; worker delegates execution to the same engine. | This is a clear orchestration/execution/transport separation. Preserve distinct return/delivery semantics. |
| C4 | **B. TRANSITIONAL BUT SAFE** | Domain quality/validation calculations use dataframe/numerical libraries; `sklearn` is isolated to anomaly detection in `domain/quality/anomalies.py`. | Current responsibility-based ownership is evidenced; do not relocate by dependency aesthetics. |
| D1 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Direct API quality/report semantics vs workflow/capability/worker paths are not universally equivalent. | Specify report/result contract and representative parity scope before route/path consolidation. |
| D2 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Cache owner, key/invalidation behavior and intended sync/worker sharing are not a complete core contract. | Do not change cache behavior until contract and tests exist. |
| D3 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Validator category/plugin/legacy fallback boundaries differ; external plugin consumers may exist. | Specify per-category and plugin contracts; retain discovery order/fallback. |
| D4 | **C. REQUIRES CONTRACT BEFORE MIGRATION** | Risk route policy freshness/lifetime differs from app-scoped service wiring. | Specify freshness semantics and test API response/error behavior before wiring change. |
| D5 | **A. INTENTIONAL COMPATIBILITY** | Full external compatibility surface of AI providers, dashboard launch paths, aliases and public imports cannot be established from repository search. | Preserve shims and entrypoints; require deprecation/consumer evidence before removal. |
| D6 | **D. BLOCKED BY EXTERNAL EVIDENCE** | Production PostgreSQL schema baseline and applied revision, production-equivalent upgrade/restore evidence, and deployment/provisioning order remain unavailable. | Local migration repair and PostgreSQL validation are complete; production migration authorization remains unestablished. |

## Production migration authorization gate — separate from architectural consolidation

Architectural consolidation, local migration repair, and production migration authorization are separate decisions. Strategy D is repaired and validated locally against the disposable PostgreSQL 16.15 database. The project has only run local/development environments; there is no production database or production data requiring preservation. This establishes the local clean-install target, not production schema equivalence or production migration safety.

```text
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
DEPLOYMENT_PROVISIONING_ORDER = INCOMPLETELY_EVIDENCED
MIGRATION_REPAIR_VALIDATION = PASS (local/disposable PostgreSQL 16)
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
```

Before production migration authorization, resolve the production-facing evidence items above, document a dedicated migration-job deployment sequence, and establish backup/restore and forward-recovery assumptions. Because the project has never been deployed, there is no historical production schema artifact or data baseline to preserve; do not invent one or treat the disposable database as production-equivalent.

The already completed local checks are recorded in the final addendum below. Never infer production readiness from SQLite, ORM metadata, the disposable PostgreSQL database, or the green unit/integration suite. No production migration or connection is authorized by this review.

## Future-facing contracts and scope guard

Future changes should preserve: owner/workspace isolation; existing API paths, response fields, status/error mapping and OpenAPI contracts; ChangeSet integrity and atomic rollback; workflow version snapshots, capability order and state transitions; queue delivery/recovery semantics; trace/report/error contracts; memory tenant/expiry/redaction behavior; channel sync idempotency and connector effects; audit/lineage transaction guarantees; and plugin/compatibility discovery order. These are constraints for future reviews, not an instruction to change code.

| Contract before future migration | Components and current ambiguity | Evidence needed | Makes a bounded migration ready when |
|---|---|---|---|
| Risk policy freshness | `api/routes/risk.py`, `get_container`, app-scoped container, `RiskRepository`, `RiskService`; per-request build reloads policy, unlike app-scoped construction. | Direct API tests and an explicit policy update/freshness expectation, including error mapping. | Route lifecycle is changed only with tested freshness and response parity. |
| Execution history/report | `api/routes/executions.py`, execution/trace repositories, workflow history, filesystem report delivery; record models and shapes differ. | Enumerated consumers and contract tests for authorization, ordering, missing records, report path/delivery and trace mapping. | One application owner can provide the existing API behavior or an explicitly approved contract transition. |
| Workflow sync/async outcome | `WorkflowRuntimeService`, `WorkflowEngine`, worker, queue, execution repositories, reports/traces. | End-to-end cases for gates, state transitions, retries/recovery (currently reclaimed work is terminally failed, not replayed), trace/report persistence and delivery. | Required semantic differences are explicit and covered for both dispatch modes. |
| Repository transaction ownership | Audit, dataset, project, workflow authoring, sync and ChangeSet persistence consumers. | Call-site transaction maps and failure-injection tests proving atomicity/commit boundaries. | Port signature makes transaction ownership explicit and parity tests cover failure/rollback. |
| Lineage transaction | `LineageTrackingService`, repository, capability and API consumers; caller can pass transaction/session context. | Consumer census and tests for caller-owned transaction commit/rollback and read scope. | Callers preserve transaction semantics through the new owner. |
| Channel sync aggregate/idempotency | `ChannelSyncService`, channel/mapping/job/attempt/project/dataset repositories and external connector. | Idempotency replay, partial failure, owner scope, mapping/attempt order, external side-effect tests. | Aggregate and compensation/retry contract is explicit and bounded. |
| Quality/report/cache/plugin | `QualityService`, data operations, direct API, capability/agent paths, validators/plugins/rules and worker. | Per-category inputs/outputs/errors, report/trace/persistence and cache invalidation tests; representative sync/worker comparison. | Selected path preserves declared category contract and fallback/discovery order. |
| Production database baseline/takeover | Alembic chain, application/worker initialization and deployment provisioning. | Authoritative PostgreSQL 16 schema/provisioning artifact; isolated baseline upgrade and empty bootstrap checks; API/worker startup and representative operation; backup/restore rehearsal; repair/reconciliation plan. | Production-equivalent lifecycle, supported deploy order and recovery are verified, not inferred from ORM or SQLite. |

No next candidate is selected. Any future candidate must begin with a fresh import/runtime-consumer census and its own preflight, tests, explicit compatibility plan and rollback. Do not broaden any of the completed slices or introduce `src/platform` for structural symmetry.

## Conditions to reopen consolidation work

Reopen this closure review only if one of these conditions is met:

1. A new concrete dependency edge is found with an already-evidenced canonical owner, known runtime consumers, behavior tests, compatibility treatment and reversible scope.
2. A defect or security/correctness issue requires a targeted change, with a test proving the intended contract.
3. The external PostgreSQL evidence gate is satisfied; this reopens database lifecycle/repair review only, not automatic architecture migration approval.
4. New evidence resolves a listed uncertain boundary (quality parity, risk policy freshness, plugin contract, or external compatibility) enough to support a specific bounded preflight.

Until then: `NEXT_CANDIDATE=NO_SAFE_NEXT_SLICE`, `PREFLIGHT=NOT_READY_FOR_PREFLIGHT`, and `NEXT_SLICE_EXECUTION=NOT_AUTHORIZED`.

## Final migration repair validation addendum — 2026-10-02

This addendum updates database-repair validation status only. The architecture decision above remains **CLOSED_WITH_DOCUMENTED_DEBT**; no new architectural migration slice is selected or authorized.

Strategy D is implemented as a single linear active Alembic graph with base/head `20261002_01`; the 23-revision historical graph is preserved in the inactive archive. Fresh install passed against the disposable PostgreSQL 16.15 database. The observed schema had 31 application tables, 43 foreign keys (all `NO ACTION`), 67 explicit/application indexes and 109 total indexes (67 explicit/application + 31 primary-key + 11 unique). Fresh seed policy passed without demo, admin, or application rows. Representative ORM persistence Groups 1–7 passed INSERT, COMMIT, and fresh-session SELECT.

The initial Group 4 failure was an application harness issue: Channel and ChannelMapping were inserted in one ORM flush without an ORM relationship. The actual repository sequence commits the Channel before the ChannelMapping and passed. The stale `20260928_01` current-head expectation in `tests/test_persistence.py` was updated to derive and validate active head `20261002_01`; its archived `20260926_01 → 20260928_01` upgrade scenario was replaced with an active clean-install lifecycle check. The production revision guard remains intact.

Final canonical regression evidence: `.\venv\Scripts\python.exe -m pytest -q` — **994 collected / 994 passed**, 0 failed, 0 errors, 0 skipped, 0 warnings, in **75.14 seconds**. Focused persistence suite: **7 passed**. `git diff --check` passed. Earlier 992-test evidence above describes the architecture audit at that time and is superseded as the latest full-suite result, not erased as historical evidence.

This disposable local validation does not prove production schema equivalence or production migration safety. Production schema baseline and applied Alembic revision remain unknown; backup/restore evidence and production-equivalent upgrade rehearsal remain unavailable; deployment/provisioning order remains incompletely evidenced.

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
