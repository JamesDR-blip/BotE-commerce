# Alembic Repair Implementation Report

**Current status (final closure, 2026-10-02):** Migration repair and local PostgreSQL 16 validation are fully validated. Production migration safety/readiness is not established.
**Authorization context:** Strategy D repair and disposable PostgreSQL 16 validation were separately authorized. Production/staging migration remains unauthorized.

## Files changed by this implementation

- Added active revision: `database/migrations/versions/20261002_01_canonical_postgresql_baseline.py`.
- Moved all 23 former `database/migrations/versions/*.py` revision files, without content edits, to `database/migrations/archive/legacy_versions/` and added `database/migrations/archive/legacy_versions/README.md`.
- Added database-free regression checks: `tests/test_migration_graph.py`.
- Updated implementation/status documentation: `MIGRATION_REPAIR_IMPLEMENTATION.md`, `MIGRATION_REPAIR_DESIGN.md`, `TARGET_SCHEMA_RECONCILIATION.md`, `SCHEMA_DECISION_REGISTER.md`, `CANONICAL_SCHEMA_CONTRACT.md`, `DATABASE_OPERATING_CONTRACT.md`, `CANONICAL_SCHEMA_RECONCILIATION.md`, `FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md`, `MIGRATION_PLAN.md`, `PRODUCTION_READINESS_DEBT_REGISTER.md`, `docs/operator/database-migration.md`, and `docs/operator/rollback.md`.
- No application source, ORM model, Alembic environment/configuration, runtime configuration, Docker file, or existing application test was modified. Pre-existing unrelated worktree changes were left untouched.

## Result

The active Alembic history is a single-root, single-head clean-install lineage. Its baseline is `20261002_01`, in `database/migrations/versions/20261002_01_canonical_postgresql_baseline.py`. The former 23 revisions were moved without content edits to `database/migrations/archive/legacy_versions/`; the archive README records their original revision IDs and explains that they are inactive historical evidence. The archive is outside Alembic's configured `versions` directory.

The new revision is a frozen set of explicit Alembic operations. It does not import ORM metadata, call `create_all()`, inspect existing tables, execute raw SQL, or insert seed data. It creates the 31 current ORM tables in dependency order, including 43 foreign keys, 67 indexes, and 11 unique constraints. The three integer primary keys use SQLAlchemy/Alembic autoincrement semantics. No server defaults, database cascades, native enums, extensions, or seed rows are introduced. Foreign keys have no explicit `ondelete`/`onupdate` action, which gives the selected PostgreSQL default `NO ACTION`.

The current ORM metadata declares 26 timezone-aware `DateTime` columns and six timezone-naive columns: `execution_traces.started_at`, `execution_traces.finished_at`, `execution_traces.created_at`, `capability_execution_traces.started_at`, `capability_execution_traces.finished_at`, and `capability_execution_traces.created_at`. The baseline follows those exact declarations. This clarifies the older inventory's broad timezone summary without changing model behavior.

`alembic.ini`, `database/migrations/env.py`, application startup, worker startup, and runtime configuration were not changed. The existing runtime head guard discovers the new single active head from the configured Alembic script directory.

## Historical archive and local database policy

The archive contains these 23 original IDs:

`0001_persistence`, `20230912_01`, `20230912_02`, `20230912_03`, `20230912_04`, `20260914_01`, `20260914_02`, `20260914_03`, `20260916_01`, `20260916_02`, `20260916_03`, `20260916_04`, `20260922_01`, `20260923_01`, `20260926_01`, `20260928_01`, `7757af5afe0a`, `b05fd7d45c87`, `c13a7e91d204`, `d14c1f2a9b31`, `e2f3a4b5c6d7`, `f3a4b5c6d7e8`, and `fcbc1a52044c`.

Archived revisions are not an active Alembic lineage, and the new active graph does not recognize their version IDs. No automated local-database transition, stamp, export/import, reset, or deletion mechanism was implemented. Existing SQLite files, persistent Compose volumes, and the PostgreSQL verification container remain untouched. Their owners must classify and back up each state before any separately authorized adoption procedure. Do not run the new `upgrade head` against a database carrying an archived revision until a state-specific path is reviewed and authorized.

## Treatment of the ten history discrepancies

| ID | Implementation treatment |
|---|---|
| H1 | The raw PostgreSQL-incompatible `DATETIME` revision is archived. The baseline declares the workspace timestamp using the current timezone-aware ORM type. |
| H2 | The conditional/duplicate workspace creators and `ws-demo` deletion behavior are archived. The baseline creates workspaces once, requires `owner_id`, and inserts or deletes no workspace data. |
| H3 | `projects` is created in the baseline. |
| H4 | `datasets` is created in the baseline before dependent tables. |
| H5 | `workflows` is created in the baseline. |
| H6 | `workflow_versions` is created in the baseline after workflows. |
| H7 | `workflow_executions` is created in the baseline before dependent history and trace tables. |
| H8 | `execution_traces` is created in the baseline. |
| H9 | `capability_execution_traces` is created in the baseline after workflow executions. |
| H10 | The conditional/partial legacy persistence creators are archived. The baseline declares complete current table definitions directly. |

The design matrix remains the detailed discrepancy record. No existing-local data migration is implied by these clean-install operations.

## Seven historical server-default behavior changes

The baseline follows the owner-approved application-side default policy. These seven persistent defaults from archived history are not server defaults in the new baseline:

- `executions.status` (historical lowercase `completed`; application behavior is uppercase `COMPLETED`)
- `risk_policies.high_risk_threshold`
- `risk_policies.critical_risk_threshold`
- `channel_mappings.external_product_id`
- `channel_mappings.last_synced_hash`
- `channel_mappings.active`
- `compliance_policies.enabled`

Application/ORM writes retain their defaults. A non-ORM writer must supply the value. The temporary approval-token backfill default is not persistent and is not a target server default. `sync_attempts.external_product_id` has no historical persistent server default.

## System seed and downgrade behavior

The baseline contains schema only. It does not seed RBAC roles, permissions, or links; it creates no administrator, identity, tenant, workspace, or demo data. The separate idempotent RBAC seed remains an operational requirement described in `SYSTEM_SEED_CONTRACT.md`, but its command/job is not implemented by this migration repair because that contract leaves the seed mechanism to a separate operation.

The baseline downgrade raises an explicit error. The approved design does not support destructive downgrade of the canonical baseline. Recovery is by a separately tested compatible application release or restoration of a matching verified database backup; no database was available or accessed to test that recovery.

## Validation performed during implementation (superseded by final closure below)

- Static Alembic `ScriptDirectory` inspection: one base, one head, one active revision; head `20261002_01`.
- Python AST syntax validation of the baseline: PASS.
- Ruff static checks for the baseline and new structural test: PASS.
- Added database-free test coverage verifies active graph/archive separation and compares all baseline table names, column names/types/nullability, primary keys, unique constraints, foreign-key pairs/actions, and indexes with current ORM metadata.
- Focused command: `venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_migration_graph.py` — **2 passed**.
- The 23 archived revision files match their repository `HEAD` content after normalizing Git checkout line endings (23/23); they were moved without content edits.
- `git diff --check` — PASS for tracked changes; added-file whitespace/newline scan — PASS.

Not performed: any Alembic command that connects to a database; `upgrade`, `downgrade`, `stamp`, `current`, database creation or SQL; PostgreSQL 16 execution; SQLite execution; application or worker startup; the full test suite; production or staging access; backup/restore testing.

## Risks identified before runtime validation (resolved or bounded by final closure below)

PostgreSQL 16 compatibility remains **UNVERIFIED**. The offline structural comparison proves alignment to current ORM metadata, not that PostgreSQL accepts the DDL, that autoincrement compiles as intended, that the schema fingerprint matches a live database, or that application/worker operations succeed. The authorized next validation must use the isolated disposable PostgreSQL 16 verification environment only after separate explicit authorization. It must cover empty database to `upgrade head`, schema inventory/fingerprint, one-row version state, repeat-upgrade no-op, representative persistence operations, application and worker startup, and the approved seed as a separate operation.

Risks that remain:

- Existing local Alembic version IDs are no longer part of the active graph; those databases require classification and a separately reviewed adoption path.
- PostgreSQL-generated DDL and three integer identity/sequence behaviors have not been exercised against PostgreSQL 16.
- The six naive trace timestamps are faithfully copied from ORM metadata; their production timestamp semantics still require owner/runtime confirmation if timezone normalization is desired.
- The full application suite was not run. The protected 992-test baseline has not been re-established as part of this migration-only task.
- The RBAC seed command/job and operational schema validation are still separate work.

## Initial PostgreSQL validation authorization and preflight — 2026-10-02 (historical; superseded)

The owner separately authorized validation against `aeop-postgres16-verify` only. The attempt stopped before connecting because Docker's Linux engine named pipe was unavailable, Docker Desktop was not running, and the named container/`localhost:55432` mapping could not be inspected. No database identity, version, emptiness, schema, or revision was checked; no Alembic command or database test was run. See [`POSTGRESQL_16_VALIDATION_REPORT.md`](POSTGRESQL_16_VALIDATION_REPORT.md). The authorization remains limited to the isolated disposable target, but execution is blocked until its identity and empty state can be verified.

```text
ALEMBIC_REPAIR_IMPLEMENTED = YES
ACTIVE_ALEMBIC_HEAD_COUNT = 1
ACTIVE_ALEMBIC_HEAD = 20261002_01
CANONICAL_BASELINE_IMPLEMENTED = YES
HISTORICAL_23_REVISIONS_PRESERVED = YES
DATABASE_ACCESSED = NO
POSTGRESQL_16_VALIDATION = BLOCKED_AT_PREFLIGHT
APPLICATION_STARTED = NO
TESTS_REQUIRING_DATABASE = NOT_RUN
IMPLEMENTATION_SCOPE = ALEMBIC_REPAIR_ONLY
NEXT_GATE = Make Docker Desktop available and repeat the isolated-container identity, port, version, and empty-database preflight
```

## Final migration repair and local PostgreSQL validation closure — 2026-10-02

The owner-authorized Strategy D repair completed validation on the existing disposable PostgreSQL 16.15 database. The active Alembic graph has one base and one head, `20261002_01`; the 23-revision former graph remains preserved in the inactive archive. Fresh `alembic upgrade head` passed. The validated schema has 31 application tables, 43 foreign keys, 67 explicit/application indexes, and 109 total indexes (67 explicit/application + 31 primary-key + 11 unique). All 43 foreign keys use `NO ACTION`. Fresh-install seed policy passed: no demo, admin, or application seed rows were created. The owner confirms the project has only run local/development environments and has never had a production or staging database; there is no historical production data/schema to preserve.

Representative ORM persistence Groups 1–7 all passed INSERT, COMMIT, and fresh-session SELECT. The earlier Group 4 `channel_mappings_channel_id_fkey` failure was a test-harness issue: the harness inserted channel and mapping in one ORM flush without an ORM relationship; the actual repository sequence commits the channel before the mapping and passed. No schema correction was required for that failure.

The stale test expectation in `tests/test_persistence.py` was corrected using the active Alembic head and a clean active-head migration lifecycle. The archived `20260926_01 → 20260928_01` path is no longer treated as an active upgrade path. The production current-revision check remains enabled and was not weakened.

Canonical regression command `.\venv\Scripts\python.exe -m pytest -q` completed with **994 collected / 994 passed**, 0 failed, 0 errors, 0 skipped, 0 warnings, in **75.14 seconds**. Focused persistence suite: **7 passed**. `git diff --check` passed. The test-only correction was limited to `tests/test_persistence.py`; no application startup behavior, ORM model, repository/service, or migration file was changed for validation. The PostgreSQL instance was disposable local verification infrastructure, not a production-equivalent database, and was not reset.

The operating model remains a dedicated migration job, followed by schema validation and then application/API and workers; application startup does not run automatic Alembic migrations. Production evidence remains unresolved: `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`; `PRODUCTION_ALEMBIC_REVISION = UNKNOWN`; `BACKUP_RESTORE_EVIDENCE = UNAVAILABLE`; production-equivalent upgrade rehearsal is unavailable; production deployment/provisioning order remains incompletely evidenced. This local validation proves neither production schema equivalence nor production migration safety.

```text
MIGRATION_REPAIR_VALIDATION = PASS
POSTGRESQL_PERSISTENCE_VALIDATION = PASS_WITH_REPRESENTATIVE_COVERAGE
FULL_REGRESSION = PASS
ACTIVE_ALEMBIC_BASE = 20261002_01
ACTIVE_ALEMBIC_HEAD = 20261002_01
ARCHITECTURE_CONSOLIDATION = CLOSED_WITH_DOCUMENTED_DEBT
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
DEPLOYMENT_PROVISIONING_ORDER = INCOMPLETELY_EVIDENCED
```
