# PostgreSQL 16 Validation Report

**Status of initial attempt:** BLOCKED AT PRE-FLIGHT — this historical attempt was superseded by the final authorized validation recorded below.
**Authorization:** Isolated PostgreSQL 16 validation only, granted by the owner on 2026-10-02.
**Scope restraint:** No production/staging endpoint, source code, model, migration, Docker configuration, or runtime configuration was accessed or changed.

## 1. Environment

- Docker client is installed at `C:\Users\Admin\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`.
- Docker daemon was unavailable. The exact client error was: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- Docker Desktop process was not running. `com.docker.service` was not found in the service inventory.
- The local listener inspection for port `55432` failed with `CimException`; no listener or port mapping could be established.
- The named container `aeop-postgres16-verify` could not be inspected because the Docker daemon was unavailable. Its running state, image, port mapping, database name, and PostgreSQL version are therefore unverified in this attempt.
- Git status was inspected before validation. The checkout contained pre-existing application/test/documentation changes and the prior Strategy D migration/archive changes. Those changes were not modified in this preflight.

## 2. Pre-flight state

The approved target is the disposable container `aeop-postgres16-verify` at `localhost:55432`. Because Docker could not establish the container identity or port mapping, the database target could not be proven to be that disposable instance. The preflight stop rule therefore applied before any database connection.

| Evidence | Result |
|---|---|
| Named container exists and is inspectable | UNVERIFIED — Docker daemon unavailable |
| PostgreSQL version is 16.x | UNVERIFIED |
| Host target is `localhost:55432` and maps to the approved container | UNVERIFIED |
| Database name and disposable ownership | UNVERIFIED |
| Database empty state | NOT CHECKED |
| Current Alembic revision before upgrade | NOT CHECKED |
| Existing table inventory before upgrade | NOT CHECKED |

## 3. Alembic upgrade and schema inspection

`alembic upgrade head` was **not run**. No database command, SQL query, authentication, Alembic `current`, schema inspection, or reset was attempted. The migration was not reported as failed; it was not attempted because the authorized target could not be verified.

The previously completed database-free graph inspection identified one active base and head, `20261002_01`. The database revision state and resulting PostgreSQL schema are unknown.

## 4. Schema, constraints, indexes, and defaults

No live PostgreSQL schema was available for comparison. The design expects 31 tables, 43 foreign keys, and 67 indexes, but these are expected contract counts, not observed database counts. Primary keys, unique constraints, FK delete actions, nullability, PostgreSQL column types, timestamp timezone behavior, JSON representation, sequences/identity behavior, and server defaults remain unverified on PostgreSQL 16.

The presence or absence of the seven historical server-default differences was not checked in a database. The baseline's static comparison to ORM metadata is recorded in `MIGRATION_REPAIR_IMPLEMENTATION.md`; it is not a substitute for PostgreSQL inspection.

## 5. Seed validation

Not performed. The database was not inspected, so required RBAC reference records, administrator credentials, demo/sample rows, and workspace seed state are unknown. No seed was run.

## 6. Representative persistence checks

Not performed. No representative organization/workspace, RBAC, dataset, workflow, execution, channel/sync, memory, ChangeSet, approval/risk, audit, or lineage operation was run.

## 7. Reproducibility

Not run. The database was not reset, dropped, or otherwise modified. A second clean-install check is not authorized until the container is confirmed and the database is proven empty/disposable.

## 8. Tests and validation

- Database validation tests: NOT RUN.
- Application persistence/integration tests: NOT RUN.
- Full test suite: NOT RUN.
- Migration-repair static tests from the prior implementation step: 2 passed; they do not provide PostgreSQL runtime evidence.
- No migration file was modified during this validation attempt.

## 9. Mismatches, failures, and next action

No migration or schema mismatch was observed because none was executed. The blocker is environmental and precedes database access: Docker Desktop's engine endpoint is unavailable, so container identity, PostgreSQL version, and port mapping cannot be verified.

Next, make the approved Docker Desktop environment available, then repeat preflight and verify the named container, PostgreSQL 16.x version, `localhost:55432` mapping, database identity, and empty state before running any Alembic command. If the database is not empty or target identity remains ambiguous, stop without modifying it. Once `alembic upgrade head` begins, any migration failure must stop the pass without patching migrations.

```text
POSTGRESQL_VERSION = UNAVAILABLE
DATABASE_TARGET = aeop-postgres16-verify
DATABASE_IS_DISPOSABLE = UNVERIFIED — container could not be inspected
ALEMBIC_UPGRADE_HEAD = NOT_RUN
ACTIVE_HEAD_COUNT = 1 (static repository graph; database state not checked)
ACTIVE_HEAD = 20261002_01 (static repository graph; database state not checked)
TABLE_COUNT = NOT_VERIFIED (expected 31)
FOREIGN_KEY_COUNT = NOT_VERIFIED (expected 43)
INDEX_COUNT = NOT_VERIFIED (expected 67)
CANONICAL_SCHEMA_MATCH = PARTIAL — static ORM/baseline match only; PostgreSQL unverified
SYSTEM_SEED_VALIDATION = NOT_RUN
REPRESENTATIVE_PERSISTENCE = NOT_RUN
REPRODUCIBILITY = NOT_RUN
DATABASE_VALIDATION = PARTIAL — preflight blocked before connection
MIGRATION_FILES_MODIFIED_DURING_VALIDATION = NO
NEXT_GATE = Make Docker Desktop available and repeat the isolated-container identity, port, version, and empty-database preflight
```

## Final authorized PostgreSQL 16 validation — 2026-10-02

The subsequent owner-authorized validation used the existing disposable `aeop-postgres16-verify` database. PostgreSQL reported version **16.15** and Alembic revision **20261002_01**. A fresh migration install completed successfully. The observed schema contained 31 application tables, 43 foreign keys, 67 explicit/application indexes and 109 total PostgreSQL indexes (67 explicit/application + 31 primary-key + 11 unique). All 43 foreign keys used `NO ACTION`. Fresh-install seed policy passed with no demo, admin, or application seed rows.

Representative ORM persistence Groups 1–7 passed INSERT, COMMIT, and fresh-session SELECT. The prior Group 4 failure was confirmed as an application test-harness issue caused by inserting Channel and ChannelMapping together in a single ORM flush without an ORM relationship. The actual repositories commit Channel first and ChannelMapping second; that path passed without a schema change.

The stale active-head expectation in `tests/test_persistence.py` was corrected. The test now derives the configured Alembic head, validates the current head `20261002_01`, and checks the active clean-install lifecycle rather than the archived `20260926_01 → 20260928_01` edge. The production revision guard remains intact. The focused persistence test passed **7/7**; the canonical full suite `.\venv\Scripts\python.exe -m pytest -q` passed **994/994** in **75.14 seconds**, with 0 failures, errors, skips, or warnings. `git diff --check` passed.

This validation is limited to the disposable local PostgreSQL environment and representative persistence paths. It does not establish an authoritative production schema baseline, production Alembic revision, production-equivalent upgrade rehearsal, backup/restore readiness, deployment ordering, or production migration safety. The initial blocked attempt above remains part of the chronology; its status is superseded by this final result.

```text
POSTGRESQL_VERSION = 16.15
DATABASE_TARGET = aeop-postgres16-verify (disposable local verification)
ACTIVE_ALEMBIC_HEAD_COUNT = 1
ACTIVE_ALEMBIC_BASE = 20261002_01
ACTIVE_ALEMBIC_HEAD = 20261002_01
FRESH_ALEMBIC_INSTALL = PASS
APPLICATION_TABLES = 31
FOREIGN_KEYS = 43 (43/43 NO ACTION)
EXPLICIT_APPLICATION_INDEXES = 67
TOTAL_POSTGRESQL_INDEXES = 109 (67 explicit/application + 31 primary-key + 11 unique)
FRESH_SEED_POLICY = PASS (no demo/admin/application seed rows)
REPRESENTATIVE_PERSISTENCE = PASS (Groups 1-7)
FULL_REGRESSION = PASS (994 collected, 994 passed, 75.14 seconds)
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
PRODUCTION_EQUIVALENT_UPGRADE_REHEARSAL = UNAVAILABLE
DEPLOYMENT_PROVISIONING_ORDER = INCOMPLETELY_EVIDENCED
PRODUCTION_MIGRATION_AUTHORIZATION = NOT_ESTABLISHED
```
