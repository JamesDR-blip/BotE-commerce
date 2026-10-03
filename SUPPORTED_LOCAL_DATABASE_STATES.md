# Supported Local Database States

**Date:** 2026-10-02

**Scope:** repository/configuration/history inventory only. No database was opened or modified; no container was inspected, created, or changed; no tests or Alembic commands were run.

**Production/staging:** per project-owner statement, none has existed. This inventory is not evidence of a production database.

## Inventory

| Source / evidence | Database type | Expected provisioning method | Known Alembic revision | Disposition | Confidence | Migration handling required |
|---|---|---|---|---|---|---|
| Existing root `.env` supplies a `DATABASE_URL` with SQLite scheme; value is not reproduced here. `configs/settings.py` defaults to `sqlite:///./data_quality.db`. | SQLite file `./data_quality.db` | In the default development environment, `services/container.py` calls `make_session_factory` with schema creation enabled; that invokes ORM `Base.metadata.create_all()`. This creates missing tables but does not reconcile arbitrary missing columns/constraints or record an Alembic revision. | Not established by `.env`. Earlier read-only evidence recorded the tracked file at `20260928_01`; this phase did not reopen it to verify current state. | **Potentially persistent / UNKNOWN.** Do not treat it as disposable: it exists, is version-controlled, and is the default path. Preserve a copy and obtain owner disposition before any schema operation. | High for configured scheme/path and tracked file; medium for provisioning due runtime environment overrides; revision is prior-report evidence only. | Inventory exact schema/version and decide whether to preserve, snapshot, recreate, or migrate. No schema action is authorized here. |
| Tracked repository artifact `data_quality.db`; `git ls-files` confirms tracking and history shows changes alongside application/model development. File metadata in this inspection: 602,112 bytes, last write 2026-09-28. | SQLite | Historical evidence shows application startup `create_all()` coexisted with later incremental Alembic revisions. Prior reports record the database as containing current ORM objects and `alembic_version=20260928_01`; no contents were read in this phase. | `20260928_01` in the prior read-only report; **not independently verified now**. | **Persistent for source-control purposes; data preservation status UNKNOWN.** Tracking does not prove user data is valuable, but it does mean changes affect the repository artifact. | High for existence/tracking/history; medium for prior revision report; no current database evidence collected. | Keep untouched. Before any future bootstrap/migration, establish whether this tracked DB is a fixture, developer data, or a distributable sample; snapshot and test against a copy. |
| `.env.example` uses an SQLite `DATABASE_URL` targeting `./data_quality.db`; `Settings` has the same fallback. | SQLite configuration example | Non-production container composition enables metadata schema creation in development; test fixtures also create metadata directly. | None specified by the example. | **Template only; database state UNKNOWN.** The example points at a filename that is also a tracked repository file, so “example” does not establish disposability. | High for config text; no actual DB-state claim. | Preserve the actual file; use only isolated test paths when tests need disposable state. Resolve whether normal developer startup should target the tracked artifact. |
| `docker-compose.yml` declares PostgreSQL 16 service `db` with named `postgres_data` volume. It interpolates `DATABASE_URL` from the host environment/`.env` before using a PostgreSQL fallback. The current `.env` sets SQLite scheme. | PostgreSQL 16 configuration plus possible SQLite application URL | PostgreSQL image initialization creates the container database; Compose has no Alembic migration service/command. Development app startup is configured to use `create_all()` when its environment is non-production. Depending on interpolation and overrides, the app may point to SQLite while the PG service also runs. | None specified; Compose does not run Alembic. | **Actual runtime state UNKNOWN.** The named volume is persistent by design; do not assume disposable based on local Compose. The current `.env` makes the PostgreSQL fallback non-operative unless overridden. | High for declared configuration; no container/database inspection performed. | If this volume exists, preserve it until owner identifies its use and Alembic state. Reconcile the effective URL and schema using an explicitly authorized read-only review later. |
| Owner-identified `aeop-postgres16-verify` container; previous repository report records PostgreSQL 16.15, database `dataquality_verify`, empty user schema, no `alembic_version`. | PostgreSQL 16 disposable verification database | Empty verification target; no schema provisioning was completed. | None, per previous report. | **DISPOSABLE_VERIFICATION** by owner/context; not staging, production, or local app data. This phase did not connect to or inspect the container. | High for owner-provided role; prior report is supporting historical evidence only. | No migration handling now. A future explicitly authorized phase may use it only as a disposable verification target; do not repurpose it as a local state baseline. |
| Test `tmp_path` SQLite databases in `tests/test_persistence.py` and other DB tests. | SQLite files under pytest temporary directories | Tests call `Base.metadata.create_all()`. `test_persistence.py` creates synthetic Alembic-version rows for current-head startup and a `20260926_01` → head test; the former is metadata-created and manually revision-marked, the latter is metadata-created and manually marked before invoking the migration in the test. | Synthetic `20260928_01` and `20260926_01` states in test code; these do not evidence a developer database. | **TEST-ONLY / DISPOSABLE** when isolated to each test’s temporary directory. | High from test source; no tests were run. | None for actual migration adoption. Keep test evidence distinct from a real Alembic-provisioned PostgreSQL schema. |
| Tests using `sqlite://` / in-memory engines (for example execution and trace persistence tests). | In-memory SQLite | Metadata `create_all()` or `make_session_factory()`; process/test scoped. | Generally none. | **TEST-ONLY / DISPOSABLE**. | High from test source. | No migration handling; not a source of PostgreSQL type, FK, or migration parity evidence. |
| `docker-compose.prod.yml`, `.env.production.example`, operator docs | PostgreSQL 16 deployment **configuration**, not an existing local database | Compose declares `postgres_data`; operator migration runbook says `alembic upgrade head`; Compose itself contains no migration job. The owner confirms no production/staging deployment exists. | Repository head `20260928_01`; not a deployed database revision. | **CONFIGURATION ONLY**, not an existing production/staging state. | High for repository configuration; production usage expressly absent per owner. | Do not inventory as an existing state. Deployment/provisioning must be separately designed and authorized. |

## Git history and persistence findings

- `data_quality.db` is tracked and has repeated commits aligned with model and feature changes. Reachable history reviewed in prior reports shows the artifact evolved during development; it does not establish which developers relied on it or whether its rows are disposable.
- Current `DATABASE_URL` and `.env.example` use SQLite file configuration. The environment template does not name an Alembic revision.
- Historical application startup used `Base.metadata.create_all()`; later migrations were added incrementally. The initial migration describes an existing execution persistence schema. This supports a historical local pre-provisioned-schema model, but does not prove that every local database was created the same way.
- Existing test code fabricates schemas/revision rows for selected contracts. In particular, `Base.metadata.create_all()` followed by a manually inserted version number is not an Alembic-created schema and must not be treated as a supported durable state.
- The current tracked database and Compose named volume are treated as **potentially persistent** until an owner confirms otherwise. No cleanup, recreate, stamping, migration, or copy operation was performed.

## Supported-state decision

The repository supports these **code paths**: SQLite development configuration with startup metadata creation; SQLite test schemas created from ORM metadata; a configured PostgreSQL 16 Compose service; and an operator-documented Alembic command. It does not establish which local persistent databases exist beyond the tracked SQLite artifact, the contents/revision of any local Compose volume, or a supported procedure for transitioning each such state to first production.

```text
SUPPORTED_LOCAL_STATE_INVENTORY = COMPLETE
RUNTIME_VOLUME_STATES = UNKNOWN
LOCAL_DATABASE_CONTENTS_INSPECTED = NO
DATABASE_CONNECTIONS_MADE = NO
ALEMBIC_COMMANDS_RUN = NO
TESTS_RUN = NO
```

## Local-state disposition review

Disposition is conservative and applies only to repository evidence. It does not claim the corresponding runtime volume/container currently exists; this review did not inspect Docker or open database files.

| State/artifact | Current classification | Safe disposition based on evidence | Reason / condition |
|---|---|---|---|
| Root `.env` and its SQLite `DATABASE_URL` | Local development configuration; may contain user-specific settings | PRESERVE | Do not rewrite or expose its value. Environment overrides and user intent are not known. |
| Tracked `data_quality.db` | Potentially persistent local data; current contents/revision unverified | PRESERVE; no migration, recreation, or deletion | It is tracked and is the configured default target. Tracking does not prove whether its records are disposable. Owner must classify it and approve a snapshot/transition plan. |
| Compose `postgres_data` named volume | Potentially persistent local PostgreSQL state; existence and contents unknown | PRESERVE if present; do not prune/recreate | Named volume configuration indicates persistence; there is no evidence that it is disposable or empty. |
| `aeop-postgres16-verify` | Owner-designated disposable verification target, based on prior report only | LEAVE UNTOUCHED in this closure; do not repurpose as baseline | Its previous empty-state evidence is historical, not freshly inspected. Any use requires a separate explicit verification authorization. |
| Per-test `tmp_path` SQLite files | Test-only transient state when created in an isolated pytest temporary directory | SAFE_TO_DISCARD after the owning test run completes | Scope is established by the test fixture. This does not apply to similarly named repository-root directories or arbitrary SQLite files. |
| In-memory SQLite test engines | Process/test-scoped state | SAFE_TO_DISCARD when the test process ends | Volatile by construction; not evidence for PostgreSQL behavior. |
| `.env.example`, `.env.production.example`, Compose and deployment declarations | Configuration/templates, not database contents | PRESERVE as configuration; no database disposition | They describe intended configuration only and do not establish actual running state. |

`SUPPORTED_LOCAL_STATE_INVENTORY = COMPLETE` continues to mean the repository-known local state sources have been inventoried. It does not mean every extant machine volume or local database has been found or classified. Persistent-state owner disposition is incomplete, so the schema readiness field is:

```text
LOCAL_STATE_DISPOSITION = INCOMPLETE
LOCAL_DATABASE_CONTENTS_INSPECTED = NO
RUNTIME_VOLUME_STATES = UNKNOWN
DATABASE_CONNECTIONS_MADE = NO
ALEMBIC_COMMANDS_RUN = NO
TESTS_RUN = NO
```

## Next gate

Before defining a canonical target schema, the owner must decide the unresolved default, FK delete/update, seed/bootstrap, and operational policies in `SCHEMA_DECISION_REGISTER.md`; identify which local persistent states are retained and provide a safe preservation/transition disposition; and authorize the isolated PostgreSQL 16 validation plan. Until then, `CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED`, `MIGRATION_STRATEGY = UNDECIDED`, and no migration or repair is authorized.
