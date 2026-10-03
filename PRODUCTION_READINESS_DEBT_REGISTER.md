# Production Readiness and Known-Debt Register

**Audit date:** 2026-10-02

**Scope:** repository evidence, current call sites, existing tests and runbooks. This audit did not change implementation code, tests, Alembic history, schemas, runtime/deployment configuration, or databases.

## 1. Executive status

Architecture consolidation remains **CLOSED_WITH_DOCUMENTED_DEBT**. The three completed bounded slices remain intact: Application Memory Persistence Port, owner-scoped sync-job status route, and ChangeSet Query Persistence Port. No next architectural migration slice meets the documented readiness criteria.

Production migration readiness remains **blocked by missing authoritative production evidence**. Strategy D now provides a locally validated clean PostgreSQL 16 baseline and representative persistence behavior, but it does not identify a production schema or applied revision, prove production-equivalent upgrade/restore, or establish deployment ordering. No production readiness or migration safety claim is made.

The final unchanged canonical suite `.\venv\Scripts\python.exe -m pytest -q` completed with **994 collected / 994 passed in 75.14 seconds**, with 0 failures, 0 errors, 0 skipped, and 0 warnings. `git diff --check` passed (exit code 0); Git printed line-ending advisories for pre-existing modified files, not whitespace errors. Earlier 992-pass figures in this register are historical audit results and are superseded as the latest regression result.

## 2. Architecture closure state

| Completed slice | Current boundary | Evidence in the checkout | Status |
|---|---|---|---|
| Application Memory Persistence Port | `application.memory.MemoryService` → application-owned port → infrastructure SQLAlchemy adapter; `repositories.agent_memory` remains a compatibility facade | Container wiring, repository/service/integration tests, compatibility import and wiring tests | CLOSED |
| Owner-scoped sync-job status route | API → `ChannelSyncService.get_sync_job` → owner-scoped persistence lookup | API owner/missing/foreign result tests and service/repository tests | CLOSED |
| ChangeSet Query Persistence Port | Application query service → application-owned port → existing repository implementation | Query service, repository, and API test coverage | CLOSED |

These closures reduce specific dependency edges. They do not establish that all layers are clean, alter database takeover status, or authorize more consolidation. The existing [Architecture Closure Review](ARCHITECTURE_CLOSURE_REVIEW.md) records `NO_SAFE_NEXT_SLICE` and `NOT_READY_FOR_PREFLIGHT`.

## 3. Phase 5 blocked state

The following are still unknown or unavailable:

- `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`
- `PRODUCTION_ALEMBIC_REVISION = UNKNOWN`
- `BACKUP_RESTORE_EVIDENCE = UNAVAILABLE`
- production-equivalent PostgreSQL 16 upgrade rehearsal = unavailable
- production provisioning and supported deployment order = incompletely evidenced
- migration repair validation = PASS locally; production migration authorization = NOT_ESTABLISHED

Pre-Strategy D repository forensics documented a 23-revision history with head `20260928_01` and a known empty-database PostgreSQL failure at revision `7757af5afe0a` on raw `DATETIME`. That is historical repository-path evidence, not production schema evidence. The former revisions are now archived and the active baseline `20261002_01` has passed fresh install validation on disposable PostgreSQL 16.15. Production schema and applied revision remain unknown.

Compose starts PostgreSQL 16 and Redis 7 but does not run Alembic. The operator migration guide says to run `alembic upgrade head`; production deployment instructions do not place that step in a complete provisioning/startup sequence. The disaster-recovery guide says backup/restore is supplied externally and provides no repository-supported restore procedure.

## 4. Known-debt register

Each row has exactly one primary status from the requested set. “Testable locally” means a repository behavior can be tested; it does not substitute for required production evidence.

| ID | Area and primary status | Evidence and affected components | Risk | Can tests close it? / external evidence? | Recommended next action |
|---|---|---|---|---|---|
| DB-1 | Production provisioning target and baseline status — **EXTERNAL_EVIDENCE_REQUIRED** | Owner confirms no production/staging deployment or production data has existed. Therefore there is no historical production schema/revision to preserve; `PRODUCTION_SCHEMA_BASELINE` and `PRODUCTION_ALEMBIC_REVISION` remain `UNKNOWN` for any future target until its approved provisioning state and migration state are established. | Future deployment could be inconsistent if target provisioning and migration-job order are not specified | The disposable PostgreSQL baseline proves the local canonical install only; it cannot establish a future production target or its operational readiness | Define the approved future deployment target, provisioning method, and revision-check procedure; do not invent or request a nonexistent historical production baseline |
| DB-2 | Empty PostgreSQL 16 Alembic bootstrap — **VERIFIED_LOCAL** | Strategy D active baseline `20261002_01` installed successfully on disposable PostgreSQL 16.15; 31 tables, 43 FKs, and expected indexes were inspected | Local clean install is proven for the selected target; this does not prove production upgrade or adoption safety | Local fresh install and representative persistence passed; production-equivalent evidence remains separate | Keep the active graph single-headed; do not infer production schema equivalence |
| DB-3 | Existing production revision / takeover / upgrade path — **EXTERNAL_EVIDENCE_REQUIRED** | Repository active head is `20261002_01`; owner states the project has never been deployed, so there is no production revision/data to preserve. Production deployment/provisioning order and production-equivalent upgrade rehearsal remain unverified. | Operational release and future deployment risk | Local disposable rehearsal does not establish production deployment safety | Obtain approved deployment/provisioning order and restore/recovery evidence before production migration authorization |
| DB-4 | Backup/restore and deployment order — **EXTERNAL_EVIDENCE_REQUIRED** | `docs/operator/disaster-recovery.md` explicitly says repository has no automated or repository-specific backup/restore procedure; Compose does not execute Alembic; deployment/runbook ordering is incomplete | Recovery-point and recovery-time assumptions are unverified; destructive migration recovery is unproven | Tests alone cannot close; operator/deployment backup and restore evidence is required | Obtain restore-tested backup evidence and approved deployment sequencing before any production operation |
| APP-1 | Application → repositories (audit, channel sync, canonical product, dataset, workspace/project, lineage, workflow authoring) — **ACCEPTED_DOCUMENTED_DEBT** | Current imports are enumerated in `ARCHITECTURE_CLOSURE_REVIEW.md`; behaviors include multi-repository orchestration, transactions, authorization, idempotency, immutable versions, or storage/tabular I/O | Boundary coupling; transaction, ownership, and side-effect drift if mechanically ported | Targeted contract tests can support an individual future slice; no production DB evidence is needed for a pure port, but each slice needs its own preflight | Defer. Require an evidenced contract and bounded consumer set for one use case; do not port repository trees |
| API-1 | `GET /channels` → repository — **ACCEPTED_DOCUMENTED_DEBT** | `api/routes/channels.py`: workspace access check precedes `ChannelRepository.list_for_owner`; response mapping omits credentials; tests cover public fields, workspace denial, owner behavior and empty/foreign cases | Direct API persistence dependency, but no canonical channel-list application owner is evidenced | Existing tests preserve behavior; they do not establish a target owner. No database schema dependency | Keep route and compatibility provider until a broader channel-catalog use case proves an owner |
| API-2 | Execution history/detail/report API → repositories/filesystem — **ACTIVE_ARCHITECTURAL_RISK** | `api/routes/executions.py` reads execution and trace repositories and resolves report files directly; legacy execution history is not established as equivalent to workflow history | Authorization, error, response and report lifecycle semantics could change if redirected without parity evidence | Focused API contract tests can strengthen evidence; no external DB required for the API contract, though existing persistence tests remain relevant | Do not redirect until a canonical read contract and authorization/report behavior are proven |
| API-3 | API → legacy data-operation/validation services — **ACCEPTED_DOCUMENTED_DEBT** | `api/routes/data.py` uses `DataOperationsService` for clean/extract and `QualityService` for validate; quality/capability flows overlap but are not proven equivalent | Input normalization, error/report behavior and validation category drift | Tests cover individual route/service/capability paths, not universal parity; no production DB evidence required for behavioral contract tests | Retain current paths. Define operation/category contracts before convergence |
| API-4 | Risk endpoint container lifetime — **ACTIVE_ARCHITECTURAL_RISK** | `api/routes/risk.py:get_container()` builds a new container per request; app startup also owns a container. `RiskService` policy comes from repository-backed wiring at construction. Intended policy freshness/lifetime is not specified by tests | Policy freshness, per-request resource construction, and divergence between endpoint and app-scoped composition | A test can close only after the expected freshness/lifetime contract is decided; no external DB needed for that decision | Do not normalize wiring until policy refresh and container lifecycle semantics are explicitly chosen |
| SVC-1 | Application → `services.*` (authorization/compliance/quota/validation/data operations) — **ACCEPTED_DOCUMENTED_DEBT** | Active callers include dataset, workflow runtime, ChangeSet mutation and capability paths; some services enforce policy, others wrap legacy behavior | Boundary coupling and behavior drift if reclassified by package name alone | Focused contracts can prove individual behavior; no DB external evidence for pure boundary work | Preserve active policy behavior; only move a service after its ownership and full consumer set are evidenced |
| SVC-2 | `services.container` composition — **VERIFIED_LOCAL** | API and worker startup use the container; adapters and application use cases are wired there. `ARCHITECTURE_CLOSURE_REVIEW.md` documents it as the observed composition root | Production runtime correctness remains distinct from locally verified wiring | Unit/container tests verify construction; production deployment evidence remains separately required for production readiness | Retain as the current composition root; avoid duplicate wiring |
| EXEC-1 | Workflow runtime, engine, queue and worker responsibilities — **VERIFIED_LOCAL** | Runtime service performs scope/policy/quota/risk/approval and dispatch; engine loads persisted plan/version and executes capabilities; queue transports execution IDs; worker claims and runs them. Async returns an execution ID and later persists terminal result/report/trace; sync returns inline | Sync/async delivery and response semantics intentionally differ; production Redis behavior is not proven by local fakes | Existing workflow, queue, worker, state and trace tests verify local mechanics; production Redis/restart rehearsal remains external operational evidence | Preserve the different delivery contracts; do not claim end-to-end production parity |
| EXEC-2 | Worker crash recovery/retry — **VERIFIED_LOCAL** | Redis pending delivery reclaim/heartbeat plus `WorkflowEngine.recover`; on reclaimed RUNNING work it conditionally marks FAILED and does not replay capability effects. Queue and async-state regression tests cover stale delivery and duplicate terminal protection | A crash can produce an explicit FAILED execution rather than automatic retry; side-effect replay is intentionally avoided. Production Redis failure/reconnect behavior remains unverified | Local regression tests prove implemented policy; production Redis and operational alerting evidence cannot be replaced by tests alone | Keep no-retry semantics unless idempotency/replay policy is separately designed; validate Redis operationally before production reliance |
| EXEC-3 | API history/report vs workflow history — **ACTIVE_ARCHITECTURAL_RISK** | Legacy routes return `ExecutionRecord` history and file-backed reports; workflow history uses workflow execution state/traces. No equivalence claim is supported | Consumer confusion, authorization/report mismatch, or accidental contract break during consolidation | Contract tests can show each API contract, but ownership/equivalence still requires a design decision | Preserve endpoints and aliases; treat as a separate bounded contract question |
| QV-1 | Quality, validation, cleaning, extraction and category parity — **ACCEPTED_DOCUMENTED_DEBT** | Active paths span `QualityService`, `DataHealthService`, `domain.quality`, `domain.validation`, capabilities, `services.validation_service`, `services.data_operations`, validators, extractors and agents. Existing tests prove selected paths only | Category-specific semantics, errors, reports, traces and persistence may differ; universal parity is unproven | Targeted parity tests can close selected operation/category contracts; no production DB evidence for purely in-memory behavior, but persistence parity needs database test evidence | Maintain path distinctions; test selected contracts before any unification |
| QV-2 | Quality cache key/invalidation contract — **ACTIVE_ARCHITECTURAL_RISK** | Prior blocker tracing did not establish a complete cache key and invalidation contract across direct API, sync and worker paths | Stale result, cross-input reuse, or false parity risk if callers share/alter cache behavior | Focused cache tests can establish local contract after expected invalidation semantics are decided; no external DB baseline required unless persistence is involved | Document key inputs, tenant/scope, rules/version, and invalidation before any cache refactor |
| QV-3 | Plugin precedence and category extensions — **VERIFIED_LOCAL** | `plugins.registry.ValidatorRegistry` discovers plugin packages before legacy `validators`; `tests/test_plugins.py` proves plugin and legacy discovery and Fashion compatibility | Local precedence mechanics are tested; business parity across every category/plugin is not | Tests verify registry behavior, not all category outputs; no external production evidence for registry contract | Preserve plugin-first fallback and compatibility imports; avoid claiming universal category equivalence |
| AI-1 | `agents/`, legacy `ai/`, Copilot/planner/provider boundary — **ACCEPTED_DOCUMENTED_DEBT** | Current internal call paths and tests cover Copilot workflow authoring/chat and agent-backed capabilities; external imports/provider configuration consumers cannot be enumerated from repository search | Provider behavior and public import compatibility may be hidden outside the repository | Internal tests do not prove external consumption/provider service availability | Preserve aliases and provider paths; seek explicit provider/API ownership evidence before removal or redirection |
| PERSIST-1 | `database.models`, `models/`, repositories, infrastructure persistence and schema aliases — **ACCEPTED_DOCUMENTED_DEBT** | ORM declarations are in `database.models`; memory and ChangeSet query ports have infrastructure/repository implementations; legacy model/API schema aliases remain | Confusing physical layout and compatibility debt; schema authority is distinct and still unknown | Tests can protect import compatibility and adapter semantics, not prove authoritative historical schema | Preserve compatibility facades; do not treat ORM metadata as production baseline |
| PLUG-1 | Rule engine, rules loading, validators/extractors extension boundary — **ACCEPTED_DOCUMENTED_DEBT** | Rule AST/evaluation, plugin discovery and category code have separate active consumers; Fashion legacy import is tested | Rule-source precedence, category divergence, and extension contracts could drift | Focused tests can prove selected contracts; no schema evidence required for pure rule evaluation | Preserve current registry and fallback until extension contracts are comprehensively mapped |
| SEC-1 | Authentication, authorization, RBAC, compliance, quota, audit and approval — **VERIFIED_LOCAL** | Code and focused/full-suite tests cover owner/workspace access, persisted RBAC/policy gates, approval, quota/compliance paths, and tamper-evident audit/ChangeSet behavior; security docs record implemented controls | Local tests do not prove deployed identity configuration, privileged-access operations, key management, retention or legal compliance | Tests verify local mechanics; production security configuration and stakeholder evidence are still required for a production sign-off | Preserve protected checks and audit flows; treat operational/security sign-off as external deployment work |
| SEC-2 | Telemetry, collectors, alerting and recovery operations — **EXTERNAL_EVIDENCE_REQUIRED** | Metrics endpoint and structured metrics are present; security sign-off says production collector/alerting and Docker runtime validation remain pending; DR docs lack restore rehearsal | Incidents may be undetected or recovery targets unmet | Unit tests cannot prove deployment collectors, alert delivery or operational response | Complete deployment validation and operator-owned alert/restore evidence |
| DOC-1 | Runbook revision reference — **CLOSED** | The stale reference was `20260923_01`; it was first corrected to `20260928_01`, then updated to the active canonical baseline head `20261002_01` when Strategy D was implemented. `docs/operator/database-migration.md` and `docs/operator/rollback.md` now identify `20261002_01`. | The repository documentation tracks the active graph; this says nothing about a database's applied revision. | Static repository graph inspection only; no production database evidence is implied. | No further runbook head correction until the active graph changes. No database was touched. |
| DOC-2 | Historical audit snapshots — **ACCEPTED_DOCUMENTED_DEBT** | `ARCHITECTURE_AUDIT.md` is dated 2026-07-30 and describes an earlier unauthenticated, synchronous prototype; later architecture inventory, security reports, Phase 5A–5D and Architecture Closure Review record subsequent changes and current blockers | Readers may conflate historical observations with present status | No test can close; document precedence/current snapshot | Keep historical artifacts; cite the latest relevant report and date when decisions change |

## 5. Local-verifiable items

The following are supported by current repository code/tests, subject to the scope of their tests:

- The three completed consolidation slices and their compatibility surfaces.
- Container construction and local application wiring through `services.container`.
- Owner/workspace checks and the owner-scoped sync-job lookup contract.
- ChangeSet query and memory persistence adapter contracts.
- Workflow state transitions, conditional terminal persistence, queue claim/ack mechanics, stale-delivery recovery behavior, and selected execution/trace paths.
- Plugin discovery precedence and the legacy Fashion import compatibility path.
- Selected quality, cleaning, validation, extraction, API, and capability behavior. This does not establish universal category or execution-mode parity.
- Local authentication/authorization, approval, quota/compliance, audit-integrity and API response behavior covered by tests.
- Current source-control whitespace check and canonical suite result recorded above.

Local verification does not establish production PostgreSQL schema state, production Redis behavior, deployment secrets, external providers, backup/restore, telemetry collector delivery, or organization-wide operational/security controls.

## 6. Targeted-work candidates

No candidate is authorized for implementation by this audit. Readiness here means only whether the candidate can proceed to an isolated preflight.

| Candidate | Status | Why it is bounded / required evidence before implementation |
|---|---|---|
| Specify and test risk-policy freshness/container lifetime | NOT_READY_FOR_PREFLIGHT | Expected policy refresh semantics are unknown. Decide per-request versus app-scoped freshness and error contract before writing a test that would encode the intended behavior. |
| Add more selected quality sync/worker/category parity tests | NOT_READY_FOR_PREFLIGHT | A representative streaming clean→validate parity path is documented, but operation/category semantics and expected reports/traces/persistence are not universal. Select one precise contract first. |
| Clarify direct execution history/detail/report API contract and access boundary | NOT_READY_FOR_PREFLIGHT | Legacy repository/file-backed response semantics have consumers, while workflow-history ownership is distinct. Inventory route authorization and report lifecycle before redirecting or consolidating. |

There is **no safe next architectural migration slice** identified. The runbook correction is documentation-only targeted work, not an architecture migration, and is not executed here.

## 7. External-evidence blockers

Smallest required evidence package before reopening the database baseline comparison:

1. A schema-only PostgreSQL 16 dump from production or explicitly approved production-equivalent staging, **or** an approved isolated PostgreSQL 16 staging database known to represent production, **or** the authoritative provisioning artifact that actually creates that baseline.
2. Provenance: environment designation/equivalence, PostgreSQL major/minor version, capture timestamp and freshness, source owner, provisioning method including whether historical `create_all()` was used, Alembic revision (or authoritative explanation if absent), required extensions, schema/search path, roles/grants inclusion, and artifact checksum.
3. Confirmation that the artifact is schema-only and contains no application row data or secrets.

After validation, the next evidence steps are to compare the observed schema and revision with repository history; verify empty and authoritative-existing baseline behavior on isolated PostgreSQL 16 databases; verify API/worker startup and representative operations; and validate backup/restore and the operator-approved deployment order. These checks do not by themselves authorize repair or production migration.

## 8. Accepted/documented debt

- Remaining application-to-repository imports are intentionally deferred per use case because their transaction, multi-aggregate, access-control, idempotency, versioning, or I/O contracts are not reducible to a mechanical port.
- Direct `GET /channels` persistence remains because no canonical application query owner is evidenced; no one-operation service is justified.
- Legacy execution history/report routes, API-to-service paths, quality/validation overlap, agent/provider aliases, ORM/model compatibility shims, and the split `repositories/` / `infrastructure/persistence/` layout remain until concrete ownership and compatibility evidence justifies a bounded change.
- `src/platform` is not proposed. No evidence supports a broad source-tree move.
- Inline synchronous workflow responses and queued asynchronous execution IDs/worker completion are different delivery contracts. Preserve them; do not describe them as identical semantics.
- The worker's no-replay recovery policy intentionally avoids repeating potentially non-idempotent capability effects. It results in an explicit failed execution after lease recovery rather than automatic retry.
- Earlier reports are historical snapshots. Use the latest dated evidence for current status without rewriting audit history.

## 9. Active architectural and operational risks

- Production migration risk remains critical and unresolved until authoritative baseline, applied revision, backup/restore, and production-equivalent rehearsal evidence exist.
- API execution history/detail/report access remains coupled to persistence and report filesystem paths; contract and access parity are not established with workflow history.
- Risk endpoint container construction and risk-policy freshness differ from app-scoped wiring; intended lifecycle is unresolved.
- Quality/validation/category/plugin/cache parity is proven only for selected paths. Do not unify or claim universal parity.
- Local worker lease/recovery tests do not prove production Redis availability, redelivery under real process/network failures, or alerting/operational recovery.
- Security control unit tests and repository scans do not prove production secret/key management, identity-provider wiring, external penetration testing, legal/privacy approval, retention policy or telemetry alert delivery. Existing security documentation explicitly leaves these activities pending.
- Runbook revision reference discrepancy should be corrected after confirming the stale value is not intentional historical context.

## 10. Test baseline

| Measure | Result |
|---|---:|
| Canonical command | `.\venv\Scripts\python.exe -m pytest -q` |
| Tests collected / passed | 994 / 994 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Warnings | 0 |
| Duration | 75.14 seconds |
| `git diff --check` | exit code 0; only line-ending advisory messages for pre-existing modified files |

This final run was against the existing worktree, which already contained previously authorized changes and test/report artifacts. The focused test correction was confined to `tests/test_persistence.py`; no application code or migration was changed for this validation. Earlier `992/195` figures above in the document history are preserved as dated snapshots, not as the latest baseline.

## 11. Reopen conditions

### Architecture consolidation

Reopen only for new repository evidence establishing at least one of:

- a bounded ownership contract with known consumers and compatibility requirements;
- a concrete targeted correctness defect;
- a contract/parity gap whose expected behavior is explicitly decided; or
- a newly discovered architectural violation with a small, reversible change surface.

Do not reopen merely to normalize directories, remove compatibility facades, or reduce import counts. Any future slice requires its own scope, tests, compatibility plan, rollback and explicit authorization.

### Phase 5 database baseline / migration work

Reopen the evidence comparison only after receiving the authoritative PostgreSQL 16 baseline/provisioning evidence with provenance described in §7. Before any repair authorization, establish the applied revision, compare schema objects, identify supported starting states, rehearse fresh and existing-state behavior on isolated PostgreSQL 16, validate API/worker startup and representative operations, and produce restore-tested backup plus rollback/forward-recovery and deployment-order evidence. Production migration remains separately unauthorized until the responsible operator explicitly authorizes it.

## 12. Recommended next action

The rollback runbook revision-reference correction is complete. Before any production migration, resolve the production-facing baseline/revision status, approved provisioning method and order, backup/restore evidence, and production-equivalent upgrade rehearsal. The owner confirms there is no historical production baseline or data to preserve; do not fabricate one. Keep architecture consolidation closed while production-readiness evidence is pending.

```text
ARCHITECTURE_CONSOLIDATION =
CLOSED_WITH_DOCUMENTED_DEBT

PHASE_5 =
PRODUCTION_MIGRATION_BLOCKED_BY_EXTERNAL_EVIDENCE

MIGRATION_REPAIR_VALIDATION =
PASS

POSTGRESQL_PERSISTENCE_VALIDATION =
PASS_WITH_REPRESENTATIVE_COVERAGE

FULL_REGRESSION =
PASS (994/994; 75.14 seconds)

PRODUCTION_SCHEMA_BASELINE =
UNKNOWN

PRODUCTION_ALEMBIC_REVISION =
UNKNOWN

MIGRATION_REPAIR_AUTHORIZATION =
GRANTED_AND_EXERCISED

PRODUCTION_MIGRATION_AUTHORIZATION =
NOT_ESTABLISHED

SAFE_NEXT_ARCHITECTURAL_SLICE =
NONE

SAFE_TARGETED_WORK =
NONE_PENDING; ROLLBACK_RUNBOOK_REVISION_REFERENCE_CORRECTION_COMPLETED

PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL =
UNAVAILABLE

DEPLOYMENT_PROVISIONING_ORDER =
INCOMPLETELY_EVIDENCED

NEXT_ACTION =
COMPLETE_PRODUCTION_DEPLOYMENT_AND_RECOVERY_EVIDENCE_BEFORE_PRODUCTION_MIGRATION
```
