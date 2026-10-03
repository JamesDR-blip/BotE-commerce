# Phase 5A — Alembic Migration Forensics

**Audit date:** 2026-10-02  
**Purpose:** repository and disposable PostgreSQL 16 evidence only. No migration was run or changed in this phase. No application code, tests, models, startup, deployment configuration, or database data was modified.

## Executive Summary

The named disposable container `aeop-postgres16-verify` is running PostgreSQL **16.15**. A read-only transaction against `dataquality_verify` confirmed database role `verify`, schema `public`, only the built-in `plpgsql` extension, **zero user tables**, no user sequences/views/enums, and no `public.alembic_version` relation. This is an empty verification database, not production evidence.

The supplied observed PostgreSQL failure is confirmed by the current migration text: `7757af5afe0a_add_workspace_ownership.py` executes raw DDL declaring `created_at DATETIME`; PostgreSQL 16 does not define the `datetime` type. The error is consistent with the recorded `psycopg.errors.UndefinedObject: type "datetime" does not exist`. The database's presently empty catalog and absent revision table match the stated post-failure state. This audit did not retry the upgrade.

The chain has additional structural problems beyond the first error:

1. The earliest ownership revision historically assumed `workspaces` already existed; current committed code tries to create it conditionally using PostgreSQL-incompatible `DATETIME`.
2. A later revision, `fcbc1a52044c`, unconditionally creates `workspaces` again after `7757af5afe0a` in the linear chain. If the earlier step creates the table, the later step conflicts.
3. `datasets`, `workflow_executions`, `workflows`, and several other ORM tables have no creation revision in the chain, while revisions alter or reference them. `d14c1f2a9b31` is the first `datasets` dependency.
4. Git history proves application `Base.metadata.create_all()` existed from the initial repository commit and that later ORM models were added while this application bootstrap path continued. It is strong evidence for historical schema provisioning intent, but **does not prove production used that path or establish its exact schema**.

Thus the migration history is **BROKEN as an empty-database PostgreSQL 16 bootstrap**, and historical starting-schema expectations remain ambiguous. Production schema remains unknown. No repair strategy is authorized or selected.

```text
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
POSTGRESQL_16_RUNTIME = VERIFIED
EMPTY_DB_ALEMBIC_BOOTSTRAP = FAIL
MIGRATION_CHAIN_INTEGRITY = BROKEN
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
PHASE_5A = INCOMPLETE
NEXT_ACTION = Obtain an authoritative PostgreSQL 16 schema-only baseline artifact with its environment and Alembic revision metadata.
```

## Current Evidence

### Disposable PostgreSQL 16 target

Read-only Docker inspection reported container `/aeop-postgres16-verify`, image `postgres:16-alpine`, state `running`. Read-only `psql` catalog queries reported:

| Attribute | Observed value |
|---|---|
| PostgreSQL | `PostgreSQL 16.15` on Alpine Linux, x86_64 |
| Database | `dataquality_verify` |
| Connected role | `verify` |
| Current schema | `public` |
| User schemas | `public` only |
| Extensions | `plpgsql` 1.0 only |
| User tables/views/sequences | 0 |
| User enum types | 0 |
| Alembic table | `to_regclass('public.alembic_version')` returned NULL; no revision recorded |

No baseline timestamp, creation method, or historical revision is encoded in that empty database. Container runtime verification only proves a compatible PostgreSQL 16 engine is available for this disposable target.

### Repository and Git state

- `alembic heads` (static graph inspection; no DB connection) reports one head, `20260928_01`.
- 23 version files form the reachable single linear chain listed below.
- Git history for `HEAD` is available. The initial application commit `b47e0d1` (2026-07-30) introduced `Base.metadata.create_all(engine)` in `database.models.make_session_factory`; the initial architecture called the factory from container/application startup. Commit `192a9ea` (2026-07-31) introduced `0001_persistence`, whose description explicitly says it adds ownership to an **existing execution persistence schema**.
- Commit `977fb44` added workspace/project/dataset/workflow ORM records; commit `9a7a57a` added the `d14c1f2a9b31` dataset storage-key migration, but no dataset-table creation migration.
- Commit `592588e` first added `7757af5afe0a` as an alteration of an assumed-existing workspace table. Commit `f2f5ec2` later added the raw `CREATE TABLE IF NOT EXISTS workspaces` block to that revision and also added the distinct `fcbc1a52044c_create_workspaces.py` revision. The latter's unconditional create follows the former in the current linear graph.
- `git log --all` could not be relied on because a local `refs/codex/turn-diffs/...` ref points to a bad object. Findings are based on readable `HEAD` history and checked-in source, not unreachable refs.
- The checkout already has unrelated modifications to `database/models.py` and `services/container.py` (production `create_schema`/revision-check wiring). These are pre-existing worktree changes and were not made or altered by this audit. Migration files themselves were unchanged by this audit.

### Observed PostgreSQL failure

The supplied disposable-run evidence identifies the first failure as `7757af5afe0a_add_workspace_ownership.py:22` on raw `created_at DATETIME NOT NULL`. The migration text and PostgreSQL 16's reported error agree. The read-only catalog inspection now confirms no revision table or user relations remain. No second upgrade attempt was made.

## Complete Migration Inventory

Tables/indexes/FKs below describe operations present in repository migration source. “Referenced” includes existing objects needed by FKs or alteration queries. PostgreSQL status is code inspection only except for the reported failure at `7757af5afe0a`.

| Revision / parent | Purpose; created / altered / referenced tables | Indexes and constraints | Dialect SQL, assumptions, confidence |
|---|---|---|---|
| `0001_persistence` / base | Conditional legacy persistence bootstrap. Creates `users`; if `executions` is absent, creates `executions`, `validation_logs`, `reports`; otherwise conditionally adds `executions.user_id`. References `users`, `executions`. | Creates user email/created indexes; execution user/category/source/created indexes; validation execution index; FK execution→user and logs/reports→execution. | SQLAlchemy types are portable. Branches are based on table existence only and do not reconcile every partially existing table/index. Description says existing schema. PostgreSQL-compatible in normal inspected branches; medium confidence due untested database branch states. |
| `7757af5afe0a` / `0001_persistence` | Adds ownership to `workspaces`; references `users`; current revision also conditionally creates `workspaces`. | Adds nullable `owner_id`, FK to users, owner index. | Raw `CREATE TABLE IF NOT EXISTS` is accepted syntax, but `DATETIME` is not a PostgreSQL type. **Observed PostgreSQL 16 failure.** The original Git-added form did not create the table and assumed it existed. High confidence. |
| `b05fd7d45c87` / `7757af5afe0a` | Enforces workspace ownership; alters `workspaces`; conditionally deletes the known `ws-demo` row if owner is NULL. | Changes `owner_id` to NOT NULL; no new index/FK. | SQL and DDL are PostgreSQL-compatible, but upgrade deletes data and can fail if other NULL owners remain. Downgrade only relaxes nullability; it does not restore deleted row. High confidence. |
| `c13a7e91d204` / `b05fd7d45c87` | Conditionally creates `agent_memory`; references `workspaces`, `users`. | Creates workspace, user, expiry, and compound scope/type/key indexes; FKs to workspace/user. | SQLAlchemy DDL is portable. Conditional table creation does not prove referenced baseline objects exist. High static confidence. |
| `d14c1f2a9b31` / `c13a7e91d204` | Alters `datasets` by adding nullable `storage_key`; references `datasets` before any migration creates that table. | No index/FK. | Portable additive column operation if table exists. **First datasets dependency; fails on an empty chain without an external/model-created datasets table.** High confidence. |
| `e2f3a4b5c6d7` / `d14c1f2a9b31` | Alters `workflow_executions` with nullable `dataset_id`; references `datasets`. | Adds FK to datasets and dataset index. | `batch_alter_table` is a standard Alembic abstraction and is normally native ALTER on PostgreSQL. Requires both tables and idempotently checks only the column, not separate FK/index state. High static confidence. |
| `f3a4b5c6d7e8` / `e2f3a4b5c6d7` | Alters `executions` with nullable `dataset_id`; references `datasets`. | Adds FK to datasets and dataset index. | Same batch/partial-state caveat; portable where prerequisites exist. High confidence. |
| `20230912_01` / `f3a4b5c6d7e8` | Creates `risk_policies` and `approvals`; later approval FK revision references `workflow_executions`. | Approval execution index is declared through indexed column; FK is added in next revision. | Portable SQLAlchemy DDL, but unguarded create assumes target tables do not already exist. High confidence. |
| `20230912_02` / `20230912_01` | Alters `approvals`; references `workflow_executions`. | Adds FK `approvals.execution_id`→`workflow_executions.id`; downgrade drops index and FK. | Portable batch operation if prior objects and expected index exist. Depends on workflow table absent from chain creation. High confidence. |
| `fcbc1a52044c` / `20230912_02` | Unconditionally creates `workspaces`; later risk-assessment revision references workflow executions. | Primary key only. Downgrade is `pass`, leaving the table in place. | SQLAlchemy types are PG-compatible, but unconditional duplicate creation conflicts with earlier `7757af5afe0a` if that creates/assumes the workspace. Strong graph-level defect; high confidence. |
| `20230912_03` / `fcbc1a52044c` | Creates `risk_assessments`; references `workflow_executions`. | Creates execution index and FK. | Portable DDL if workflow table exists; chain has no workflow-execution creator. High confidence. |
| `20230912_04` / `20230912_03` | Alters `approvals` with `token_hash`, then removes server default. | No index/FK. | Portable batch alteration; requires approvals and supports a pre-existing column state only as represented by migration assumptions. High confidence. |
| `20260914_01` / `20230912_04` | Creates `changesets` and `changeset_items`; references `datasets`, `executions`, `workflow_executions`, `workflows`, `changesets`. | Five changeset indexes plus item changeset index; FKs to the referenced tables. | `sa.JSON` is portable PostgreSQL JSON; no PostgreSQL-specific extension required. Depends on several tables not created by the chain. High confidence. |
| `20260914_02` / `20260914_01` | Alters `approvals`; references `changesets`. | Adds `changeset_id`, index, FK; downgrade reverses them. | Portable batch alteration if approval table and expected state exist. High confidence. |
| `20260914_03` / `20260914_02` | Creates `data_lineage_events` and `audit_events`; references datasets, workflow executions, workflows, workspaces, users, changesets. | Creates four lineage indexes and seven audit indexes; declares corresponding FKs. | SQLAlchemy JSON/date/string DDL is portable. Baseline dependencies include tables missing from the chain. High confidence. |
| `20260916_01` / `20260914_03` | Creates `channels`; references `workspaces`. | Workspace and created-at indexes; FK to workspaces. | Portable. Requires workspace state consistent with the conflicting earlier/later revisions. High confidence. |
| `20260916_02` / `20260916_01` | Creates `sync_jobs`, `sync_attempts`; references workspaces, datasets, channels, sync jobs. | Five job indexes and three attempt indexes; FKs to workspace/dataset/channel/job. | Portable. Depends on datasets and workspace baseline. High confidence. |
| `20260916_03` / `20260916_02` | Creates `channel_mappings`; references channels. | Channel, canonical product, created-at indexes; FK to channels. | Portable. High confidence. |
| `20260916_04` / `20260916_03` | Creates organizations, roles, permissions, role_permissions, memberships; alters `workspaces` with organization_id. | Organization and four membership indexes; role/permission, membership user/org/role, workspace-org FKs. | Portable DDL; requires users and workspaces. Workspace alteration assumes organization_id absent and expected table/constraint state. High confidence. |
| `20260922_01` / `20260916_04` | Creates `organization_quotas`; references organizations. | Organization index and FK. | Portable. High confidence. |
| `20260923_01` / `20260922_01` | Creates `compliance_policies`; references organizations. | Organization index and FK; JSON condition. | Portable PostgreSQL JSON/boolean defaults. High confidence. |
| `20260926_01` / `20260923_01` | Adds `changesets.integrity_hash`, reads existing changeset fields, computes and writes hashes, makes hash NOT NULL. | No index/FK. | Bound SQL with named parameters and Python hashing are portable. Requires changesets and all selected columns. Data backfill and NOT NULL precondition are material. High confidence. |
| `20260928_01` / `20260926_01` | Reads changesets and `changeset_items`, hashes item snapshots, updates integrity hashes. | No index/FK. | SQL and bound parameters are portable; JSON snapshot decoding handles string values. Requires both tables and expected columns. High confidence. |

No migration contains a PostgreSQL extension declaration, a PostgreSQL enum declaration, MySQL-only DDL, SQLite-only `INSERT OR ...`, or dialect-specific `AUTOINCREMENT` text. SQLAlchemy `DateTime`, `JSON`, booleans, integer autoincrement, and Alembic batch operations are portable at the abstraction level. The raw `DATETIME` token is the confirmed PG incompatibility; missing/duplicate-object assumptions are separate logical failures, not dialect incompatibilities.

## Table Provenance Matrix

“Outside Alembic” means repository-history evidence that evolving ORM metadata plus application `create_all()` could create a table. It does **not** mean evidence that production did so. Names in parentheses are requested aliases that do not match the repository's actual table names.

| Table | First referenced | First created by Alembic | First altered | Created outside Alembic? | Confidence |
|---|---|---|---|---|---|
| `users` | `0001_persistence` | `0001_persistence` conditionally | `0001` is conditional; later FKs | Historically possible via model metadata only after model existed; migration itself creates users | High for migration; low for production |
| `workspaces` | `7757af5afe0a` | Current `7757` conditional raw SQL; later `fcbc1a52044c` unconditional | `7757` owner; `b05` nullability; `20260916_04` organization | Yes, historical ORM `create_all()` could create it once model was added | High; lifecycle contradictory |
| `datasets` | `d14c1f2a9b31` | **None found** | `d14` storage_key; later FK references | Yes, `DatasetRecord` is in ORM metadata and historical app calls `create_all()` | High for omission; production unknown |
| `workflow_executions` | `e2f3a4b5c6d7` (also later FKs) | **None found** | `e2f3` dataset_id | Yes, ORM metadata and historical create_all path | High for omission |
| `validation_executions` | No exact table reference found | None | None | No model/table declaration found; likely terminology mismatch, not proven persistence table | High search confidence |
| `agent_memory` | `c13a7e91d204` | `c13` conditional | None later | Also represented in ORM metadata | High |
| `approvals` | `20230912_01` | `20230912_01` | `20230912_02`, `20260914_02`, `20230912_04` | ORM metadata also could create on feature-era startup | High |
| `risk_policies` | `20230912_01` | `20230912_01` | None | ORM metadata also could create | High |
| `risk_assessments` | `20230912_03` | `20230912_03` | None | ORM metadata also could create | High |
| `changesets` | `20260914_01` | `20260914_01` | `20260926_01` integrity hash | ORM metadata also could create after feature introduction | High |
| `changeset_items` (`change_set_items`) | `20260914_01` | `20260914_01` | Read for integrity; no table alteration | ORM metadata also could create | High |
| `channels` | `20260916_01` | `20260916_01` | None | ORM metadata also could create | High |
| `channel_mappings` | `20260916_03` | `20260916_03` | None | ORM metadata also could create | High |
| `sync_jobs` | `20260916_02` | `20260916_02` | None | ORM metadata also could create | High |
| `sync_attempts` (`sync_job_attempts`) | `20260916_02` | `20260916_02` | None | ORM metadata also could create | High |
| `data_lineage_events` (`lineage`) | `20260914_03` | `20260914_03` | None | ORM metadata also could create | High |
| `audit_events` | `20260914_03` | `20260914_03` | None | ORM metadata also could create | High |
| `organizations` | `20260916_04` | `20260916_04` | Referenced by later tables | ORM metadata also could create | High |
| `organization_quotas` (`quotas`) | `20260922_01` | `20260922_01` | None | ORM metadata also could create | High |
| `compliance_policies` | `20260923_01` | `20260923_01` | None | ORM metadata also could create | High |
| `executions` | `0001_persistence` | `0001` conditionally | `0001` user_id; `f3` dataset_id | Yes from original model metadata/create_all | High |
| `validation_logs` | `0001_persistence` | `0001`, only when executions absent | None | Yes from original model metadata/create_all | High |
| `reports` | `0001_persistence` | `0001`, only when executions absent | None | Yes from original model metadata/create_all | High |
| `workflows` | `20260914_01` | **None found** | None | Yes, ORM metadata and historical create_all path | High for omission |
| `projects` | No migration reference as a created table; model/repository use | **None found** | None | Yes, ORM metadata and historical create_all path | High for omission |
| `workflow_versions` | No migration creates it; model/repository use | **None found** | None | Yes, ORM metadata and historical create_all path | High for omission |
| `execution_traces` | No migration creates it | **None found** | None | Yes, ORM metadata and historical create_all path | High for omission |
| `capability_execution_traces` | No migration creates it | **None found** | None | Yes, ORM metadata and historical create_all path | High for omission |
| `roles`, `permissions`, `role_permissions`, `memberships` | `20260916_04` | `20260916_04` | None | ORM metadata also could create | High |

Other current ORM declarations are included above where relevant; the complete declared names are visible in `database/models.py`. A provenance entry for ORM metadata is not proof of any production object.

## Baseline Assumption Matrix

| Migration | Requires pre-existing object/state? | Object | Evidence | Confidence |
|---|---|---|---|---|
| `0001_persistence` | No for its absent-table branch; yes for coherent partial/existing-table branches | Existing `executions` structure and compatible indexes/columns; users created first if absent | Inspects table names and checks only selected columns; if executions exists it does not create missing reports/logs or reconcile all indexes | High |
| `7757af5afe0a` | Historically yes; current version attempts conditional create but still needs users and no existing `owner_id` | `workspaces`, `users` | Original Git-introduced revision only batch-altered workspaces; later raw DDL is invalid on PostgreSQL 16 | High |
| `b05fd7d45c87` | Yes | `workspaces.owner_id`, rows satisfying NOT NULL after delete | Executes targeted DELETE then alters column non-null | High |
| `c13a7e91d204` | Yes | `users`, `workspaces` | Agent memory FKs point to both | High |
| `d14c1f2a9b31` | **Yes** | `datasets` with inspectable columns | Calls `get_columns("datasets")`; no table-creation revision exists | High |
| `e2f3a4b5c6d7` | **Yes** | `workflow_executions`, `datasets` | Inspects workflow table and creates FK to dataset | High |
| `f3a4b5c6d7e8` | **Yes** | `executions`, `datasets` | Inspects execution columns and creates FK | High |
| `20230912_01` | No for create itself; assumes target table names do not already exist | `risk_policies`, `approvals` | Unconditional `create_table` calls | High |
| `20230912_02` | **Yes** | `approvals`, `workflow_executions`, expected index | Batch FK references workflow execution; drops expected index on downgrade | High |
| `fcbc1a52044c` | Requires workspaces not to exist | `workspaces` | Unconditional create; earlier 7757 in same chain already creates or requires it | High |
| `20230912_03` | **Yes** | `workflow_executions` | Risk-assessment FK target | High |
| `20230912_04` | **Yes** | `approvals` | Batch add/alter token_hash | High |
| `20260914_01` | **Yes** | `datasets`, `executions`, `workflow_executions`, `workflows` | Changeset FKs | High |
| `20260914_02` | **Yes** | `approvals`, `changesets` | Adds approval→changeset FK/index | High |
| `20260914_03` | **Yes** | datasets, workflow_executions, workflows, workspaces, users, changesets | Lineage/audit FKs | High |
| `20260916_01` | **Yes** | workspaces | Channel FK | High |
| `20260916_02` | **Yes** | workspaces, datasets, channels | Sync-job FKs | High |
| `20260916_03` | **Yes** | channels | Channel-mapping FK | High |
| `20260916_04` | **Yes** | users, workspaces | Membership/workspace organization FKs | High |
| `20260922_01` | **Yes** | organizations | Quota FK | High |
| `20260923_01` | **Yes** | organizations | Compliance-policy FK | High |
| `20260926_01` | **Yes** | `changesets` plus listed hash input columns | Backfill SELECT and NOT NULL alteration | High |
| `20260928_01` | **Yes** | `changesets`, `changeset_items` and expected columns | Reads item snapshots and writes combined hashes | High |

## PostgreSQL Compatibility Matrix

| Migration | PostgreSQL-compatible? | Problem / evidence | Repair severity |
|---|---|---|---|
| `0001_persistence` | SQLAlchemy DDL is compatible; state-dependent | Conditional table logic misses partial-state reconciliation. | Medium; baseline-state-dependent |
| `7757af5afe0a` | **No** | Raw `created_at DATETIME` fails on PostgreSQL 16 with reported undefined type. | Critical; first observed failure |
| `b05fd7d45c87` | Syntax compatible; data-dependent | Deletes `ws-demo` and requires remaining owners non-NULL. | High data-safety concern |
| `c13a7e91d204` | Yes, conditional on prerequisites | FKs require users/workspaces. | Medium |
| `d14c1f2a9b31` | DDL portable; chain prerequisite fails | Requires absent datasets table. | Critical bootstrap gap |
| `e2f3a4b5c6d7` | Portable when prerequisites exist | Missing workflow_executions/datasets creators; partial schema state not fully checked. | High |
| `f3a4b5c6d7e8` | Portable when prerequisites exist | Requires datasets. | High |
| `20230912_01` | Yes, with clean target objects | Unconditional duplicate create possible on pre-provisioned schema. | High state-dependent |
| `20230912_02` | Yes, with prerequisites | Requires workflow_executions plus expected approval state. | High |
| `fcbc1a52044c` | DDL syntax compatible; chain logic is not | Unconditional duplicate workspace create after 7757. Downgrade does nothing. | Critical logical chain defect |
| `20230912_03` | Yes, with prerequisites | FK target workflow_executions absent from migration creators. | High |
| `20230912_04` | Yes, with prerequisites | Batch alteration requires approval table. | Medium |
| `20260914_01` | Yes, with prerequisites | Portable SQLAlchemy JSON; references multiple non-created tables. | High |
| `20260914_02` | Yes, with prerequisites | Approval and changeset state must match. | Medium/high |
| `20260914_03` | Yes, with prerequisites | JSON/date/FK/index DDL portable; requires several baseline tables. | High |
| `20260916_01` | Yes, with prerequisites | Requires workspaces. | Medium/high |
| `20260916_02` | Yes, with prerequisites | Requires workspaces, datasets, channels. | High |
| `20260916_03` | Yes, with prerequisites | Requires channels. | Medium |
| `20260916_04` | Yes, with prerequisites | Requires users/workspaces and compatible nullability/data. | High |
| `20260922_01` | Yes, with prerequisites | Requires organizations. | Medium |
| `20260923_01` | Yes, with prerequisites | Requires organizations. | Medium |
| `20260926_01` | Yes, with prerequisites | Backfills all existing rows then makes hash required; depends on expected columns. | High data-validation requirement |
| `20260928_01` | Yes, with prerequisites | Reads changeset items and JSON snapshots; depends on expected rows/columns. | High integrity-data requirement |

Only `7757af5afe0a` has a confirmed PostgreSQL-specific parse/type failure. Duplicate table creation, missing prerequisites, and destructive/update behavior are cross-dialect logical/data risks, not evidence of other PG-only syntax problems. Batch mode is not itself identified as incompatible; its actual execution in PostgreSQL was not reached or separately tested here.

## Workspace Timeline

1. **2026-07-30, `b47e0d1`:** initial SQLAlchemy `Base` and execution/log/report records added; `make_session_factory()` called `Base.metadata.create_all(engine)`.
2. **2026-07-31, `192a9ea`, `0001_persistence`:** conditional user/execution/log/report creation and execution ownership added. Its migration title says “existing execution persistence schema.” It does not create workspaces.
3. **2026-08-20, `977fb44`:** workspace/project/dataset/workflow ORM models and repositories added. With the historical startup call, those tables were creatable by current application metadata; no production deployment proof follows from that fact.
4. **2026-09-04, `592588e`, `7757af5afe0a`:** migration originally only altered an existing workspaces table to add nullable owner/FK/index. This is the earliest clear migration dependency on a table not created by prior revision `0001`.
5. **2026-09-04, `5373cdf`, `b05fd7d45c87`:** deletes only a `ws-demo` row with NULL owner, then makes ownership non-null. The deleted row is not recreated on downgrade.
6. **2026-09-13, `f2f5ec2`:** adds raw conditional workspace creation with SQLite/MySQL-style `DATETIME` to `7757`; also adds separate `fcbc1a52044c_create_workspaces.py`, which is later in the graph and unconditionally creates the same table.
7. **2026-09-10, `c13a7e91d204`:** agent memory requires workspace/user tables.
8. **2026-09-14, `20260914_03`:** lineage/audit migrations reference workspace/user and other pre-existing application tables.
9. **2026-09-16, `20260916_04`:** organization RBAC adds `workspaces.organization_id`.

**Conclusion:** the chain does not express one coherent workspace lifecycle. It reflects an assumed preexisting table, a later conditional-creation patch, and a second unconditional create revision. The PG failure occurs before the later duplicate-table point. Historical `create_all()` explains a plausible source for a preexisting table; it does not reconcile the duplicate migration or identify actual production state.

## Dataset Timeline

1. Initial models evolved from execution-only persistence.
2. **2026-08-20, `977fb44`:** `DatasetRecord` is introduced in `database.models`; the initial application factory still invokes metadata `create_all`.
3. **2026-09-11, `9a7a57a`, `d14c1f2a9b31`:** adds `datasets.storage_key` only. It inspects the existing table; it does not create it.
4. `e2f3a4b5c6d7` adds `workflow_executions.dataset_id` and FK to datasets.
5. `f3a4b5c6d7e8` adds `executions.dataset_id` and FK to datasets.
6. Later ChangeSet, lineage, and sync migrations also reference datasets.

No migration in the 23-file chain creates `datasets`. Earliest dependency is `d14c1f2a9b31`; this is a confirmed omitted baseline object for empty-chain purposes. Historical ORM `create_all()` is a repository-evidenced way the table could have existed in an application-created database, not proof it existed in production.

## Users / Identity Timeline

- Initial 2026-07-30 ORM persistence had execution/log/report models and historical `create_all`; the original code snapshot did not yet have the later user entity.
- `0001_persistence` introduced a conditional `users` creator and user ownership for executions. This is the first migration-created users table, not an external users provisioning step.
- `7757af5afe0a` adds workspace owner FK to users; later memory and membership tables depend on users.
- Current worktree `database.models` includes users and later identity/RBAC tables. `models/database.py` is a compatibility re-export; `models/domain.py` re-exports domain value objects, not schema metadata.
- No evidence shows users had to pre-exist `0001` on its clean branch. Existing `executions` schemas may take a different conditional branch and still require exact baseline compatibility. Production user table state remains unknown.

## ORM vs Alembic Analysis

`database/migrations/env.py` sets `target_metadata = Base.metadata`; this makes ORM metadata available to Alembic tooling but does not make migrations equivalent to `create_all()` or automatically add omitted tables during `upgrade`.

Repository ORM metadata declares tables absent from any creation revision, including `datasets`, `workflow_executions`, `workflows`, `projects`, `workflow_versions`, `execution_traces`, and `capability_execution_traces`. Migrations subsequently alter/reference several of these. Conversely, the migration history contains duplicate workspaces creation and has historical revisions/data behavior not derivable merely from the final ORM declarations. Therefore the repository model/migration relation is a **mixture**: final ORM metadata describes a broader/current object set, while the Alembic chain is a partial additive history whose correct starting schema is not encoded. The ORM is not promoted as authoritative historical DDL.

The actual disposable PostgreSQL target currently has no schema objects to compare. Production-vs-model differences, every column/index/FK discrepancy, all enum types, and seed/reference data are **UNKNOWN**, not “no difference.”

`models/database.py` is a compatibility re-export of a small legacy model set; `models/domain.py` re-exports domain values and has no persistence DDL. Repositories consume ORM models and do not define an independent complete schema. Domain objects are not database schema sources.

## `create_all()` / Bootstrap History

Static search and Git history show:

- The initial 2026-07-30 commit added `Base.metadata.create_all(engine)` directly to `make_session_factory`; container/application startup called it.
- It remained in subsequent repository history as ORM records such as workspaces, datasets, workflows, execution traces, and later persistence models were added.
- `0001_persistence` arrived the next day as an incremental revision explicitly describing an existing execution schema. This is strong evidence that application metadata bootstrap historically coexisted with an incremental Alembic history in the codebase.
- Later feature commits update the tracked local `data_quality.db` alongside models, but that local tracked artifact is not production evidence.
- Current worktree modifications change `make_session_factory` to support `create_schema=False`/revision checking and make container production startup opt out of schema creation. This is pre-existing uncommitted work in the shared checkout. It is not part of migration history and does not prove how any production database was provisioned.
- Tests separately use `Base.metadata.create_all` for test databases. This creates test schemas; it is not proof of a production schema baseline.
- `create_all()` creates absent metadata tables, not missing columns/FKs/indexes in existing tables and not Alembic revision state. The full current metadata could also precreate objects that older unguarded `create_table` revisions later try to create.

**Historical inference:** the codebase had a plausible app-startup-created schema path and then accumulated additive migrations on top of evolving ORM schemas. **Unknown:** whether production actually used this mechanism, what exact metadata version it used, when Alembic became authoritative, and which revision (if any) corresponds to production's baseline.

## Deployment / Migration Sequence Analysis

- Development and production Compose declare PostgreSQL 16. Production Compose starts Postgres/Redis and application services with health dependencies; it does **not** invoke `alembic upgrade` or a schema provisioning job.
- `docs/operator/database-migration.md` says to confirm a backup and run `alembic upgrade head` through the deployment environment. `docs/production-deployment.md` describes Compose config/build/up steps but no explicit migration stage. `docs/operator/disaster-recovery.md` says the repository has no automated backup/restore and relies on deployment-provided backups.
- Current shared worktree startup wiring disables `create_all` in production and requires the current Alembic revision; production startup therefore expects the schema already migrated. This is current local code evidence, not deployed runtime evidence.
- The supported production sequence `provision database → establish exact baseline → backup → Alembic upgrade → API/worker startup` is not fully specified or verified. No backup/restore rehearsal or PostgreSQL application operation is evidenced.
- CI `.github/workflows/ci.yml` has no PostgreSQL service/container configuration and no PG migration integration job.

## Confirmed Facts

- PostgreSQL 16.15 is running in the explicitly named disposable container; only read-only catalog queries were run.
- `dataquality_verify` currently has no user tables or enum types, only `public` user schema, `plpgsql` 1.0, and no Alembic revision table.
- Repository Alembic graph has one head `20260928_01` and 23 revision files.
- Empty-database migration failure at `7757` due `DATETIME` was previously observed and supplied by the user; source text confirms the cause. No retry occurred in this phase.
- `0001` conditionally creates users/executions/logs/reports but does not create workspace, dataset, project, workflow, or workflow-execution schema.
- Current chain creates workspace conditionally at `7757` and later unconditionally at `fcbc1a52044c`.
- No migration creates `datasets`.
- Historical application startup used `Base.metadata.create_all()` from the initial commit; no evidence proves production used it.
- `b05fd7d45c87` deletes the `ws-demo` row under a predicate and downgrade does not restore it.
- Current production deployment docs/runbook do not encode a complete provisioning/migration/backup/startup order.

## Inferences

- The chain was historically intended to upgrade a pre-provisioned evolving application schema, not to serve as a self-contained empty-PostgreSQL baseline. Evidence: initial `create_all` startup, `0001`'s “existing schema” purpose, workspace revision precondition in original commit, missing dataset creator, and later FK dependencies on model-only tables. Confidence: **high for repository historical intent**, **low for actual production provisioning**.
- The addition of the raw workspace DDL appears to have been an attempt to support a missing workspace table, but its PG type is invalid and the same commit added a later duplicate creator. This is an inference from the diff and commit contents, not documented intent.
- On the supplied empty-database run, PostgreSQL transactional DDL and current empty catalog are consistent with the failed upgrade rolling back earlier `0001` work. The database has not been altered by this audit; rollback causality is inferred, not independently replayed.

## Unknowns

- Authoritative production schema and engine instance identity/state.
- Whether production ever used `create_all`, and at which model version.
- Current production Alembic revision and whether it was stamped/adopted.
- Whether production contains `datasets`, workspace, workflow, user, or other objects with divergent columns/constraints/data.
- Required PostgreSQL extensions, schemas, seed/reference rows, ownership/grants, indexes and enums in production.
- Whether production already applied `7757`, `fcbc`, or later revisions and whether the duplicate-table path has been encountered or bypassed through a different starting revision.
- Supported backup/restore, rollback, provisioning and deployment order.
- History in broken/unreachable Git refs; the reachable `HEAD` history is available, but `--all` enumeration reports a bad ref object.

## Evidence Gaps

The disposable PostgreSQL target proves engine access and the empty failed-bootstrap state only. It is not production-equivalent schema evidence. The current no-table inventory cannot reveal expected production columns, data transformations, extension usage, migration state, grants, or backup posture. A trustworthy production-equivalent PostgreSQL 16 schema-only artifact plus its revision/provisioning metadata is still required. No SQLite artifact is used to fill this gap.

## Phase 5A Decision

**PHASE_5A = INCOMPLETE**. Repository-side history forensics establish the first PG failure and multiple chain assumptions/contradictions, and the disposable runtime state is verified. Exact historical production baseline, schema comparison, existing-baseline upgrade, restore safety, and a safe repair that preserves production data remain unprovable. `REPAIR_AUTHORIZATION = NOT_AUTHORIZED`; do not implement any strategy until external baseline evidence is obtained and reviewed.
