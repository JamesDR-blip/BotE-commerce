# Single-Head Clean-Install Alembic Repair Design

**Status:** DESIGN COMPLETE — NOT IMPLEMENTED  
**Scope:** PostgreSQL 16 first-install graph and controlled treatment of local databases. No migration/source/model/test/runtime file was changed. No Alembic command, test, database access, or application startup was performed.

**Implementation status:** The authorized Strategy D repair has since been implemented and statically validated. This document remains the approved pre-implementation design snapshot; see [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md) for actual files and validation results. PostgreSQL 16 execution remains unvalidated and unauthorized.

## 1. Executive decision

Select **Strategy D — replace/rebuild the active migration chain while preserving a documented historical archive**.

The active Alembic script location will contain a new, linear, single-head history rooted at one explicit canonical baseline revision. The existing 23 connected revisions will be retained unchanged as an immutable archive outside Alembic’s active `versions` location. The baseline will express the already-defined 31-table PostgreSQL 16 target through Alembic operations, not `Base.metadata.create_all()`, raw dialect-specific SQL, or seed data.

This is the recommended design because the current history cannot bootstrap an empty PostgreSQL 16 database, contains table operations with missing predecessors, has contradictory workspace operations including a destructive data change, and cannot safely be assumed to represent local databases created with `create_all()`. There has never been production/staging state or production data to preserve. Local data may still matter and is handled by explicit inspection, backup, and controlled adoption rules below.

This decision defines a migration design only. It does not authorize archive moves, revision creation, stamping, database work, or tests.

## 2. Strategy evaluation

| Strategy | Graph shape / heads | Fresh-install behavior | Existing local DB / version state | Startup compatibility | Complexity / rollback | PG16 reproducibility | Silent schema-change risk | Decision |
|---|---|---|---|---|---|---|---|---|
| **A. Repair existing 23-revision chain in place** | Preserve existing root and append linearly; can retain one head. Would require edits to old revision behavior plus new repair revisions. | Requires correcting the early `DATETIME` operation and workspace creation ordering; later repairs cannot help if the graph fails before reaching them. Missing tables must exist before earlier dependent revisions run. | Keeps old revision IDs recognizable, which helps existing stamped DBs. But already-applied DBs do not rerun edited historical revisions; new forward repair logic must reconcile their actual schema/data. | Current dynamic single-head check can remain compatible after head advances. | High; history edits create different outcomes for old DBs and fresh installs. Rollback would require both source and database state matching; destructive `b05...` behavior must be removed or compensated. | Possible, but only after extensive in-place conditionals and branch-state coverage. | High: one revision ID could mean different resulting schema depending on whether it was applied before or after edits and what objects existed. | **Rejected.** Preserving version IDs does not make the path deterministic; dependencies occur before a safe repair point and prior state is unknown. |
| **B. Preserve old lineage and introduce a second active clean-install lineage** | Two roots/lineages, normally multiple active heads unless merged or branched with special semantics. | Could make a separate baseline path, but Alembic cannot simply select it while retaining the old path as an active head under the runtime’s single-head assumption. | Old DB revisions remain recognized; version state becomes branch-dependent. | Conflicts with `ScriptDirectory.get_current_head()` expecting one head; no evidence runtime handles multiple heads. | High operational and rollback complexity; merge revisions do not make a broken old root disappear from an empty upgrade. | Could be made to work with special selectors but not justified here. | High: deployments could choose different heads or fail to know which path was applied. | **Rejected.** It violates the single-head contract or requires unproven runtime changes. |
| **C. Add a canonical baseline and controlled handoff while keeping the old graph active** | A new disconnected baseline creates another lineage/head; connecting it after the old head means a fresh install still traverses the broken ancestors. | Does not bypass the broken chain unless the old lineage is retired or altered. | Handoff/stamp could map old states, but the existing active graph still exposes incompatible revisions. | Single-head requirement is not met without retiring the old lineage; a merge would not solve empty-path failure. | Medium-high; controlled stamping is risky when local schemas were made by `create_all()`. | Not deterministic as a stand-alone active graph. | High if baseline stamps are accepted without a full schema fingerprint. | **Not selected separately.** Once the old graph is retired and preserved as an archive, this becomes Strategy D. |
| **D. Rebuild active history and preserve old history as an archive** | New active root at one canonical baseline; future revisions form one linear chain and exactly one head. Old 23 revisions are retained verbatim outside the active script location. | Empty PostgreSQL 16 DB applies the baseline and any linear descendants; no old revision is executed. Repeat `upgrade head` is a no-op. | Old revision IDs are intentionally not auto-upgraded in the new active graph. Every existing local DB must be categorized and either proven equivalent for a controlled handoff or migrated/exported with an explicit per-state plan. | One active head keeps the existing application’s single-head expectation. New code calculates that head from the active script directory; no app-startup migration is added. | Higher one-time adoption complexity, lower fresh-install ambiguity. Rollback for existing data is restore-from-backup; automatic downgrade is not supported. | Highest: one baseline is compiled/validated against pinned PG16 and becomes the only clean-install route. | Contained by archiving the old chain, a schema fingerprint gate, and no automatic stamping/migration of local DBs. | **SELECTED.** |

## 3. Required clean-install invariant

```text
verified empty PostgreSQL 16 database
    -> one dedicated Alembic migration job
    -> one active revision path, one active head
    -> canonical 31-table schema and constraints
    -> schema fingerprint/revision validation
    -> separate idempotent RBAC system-reference seed
    -> API/application starts
    -> workers start
```

The active graph must be deterministic, repeatable, independent of pre-existing tables, SQLite, ORM `create_all()`, and application startup. Alembic operations define schema; migrations contain no demo/admin/business seed. A second `upgrade head` on the validated target performs no schema changes.

## 4. Selected single-head and baseline design

### Active graph

- The active Alembic `versions` directory has one root: a new canonical baseline revision.
- That baseline creates the full canonical schema with explicit Alembic operations in dependency order, including all 31 tables, 43 FKs, indexes, unique constraints, and integer identity/sequence behavior.
- All 41 Python defaults remain application-side. The seven historical persistent server-default differences are intentionally absent from the baseline; direct non-ORM inserts must supply the values.
- All 43 FKs use `NO ACTION`; no database cascade is created from ORM cascade configuration.
- Any later schema changes append as a single linear descendant. No second active root, branch, or unresolved merge head is allowed.
- The active graph must make `alembic heads` return exactly one revision. The immutable head revision ID is assigned during authorized implementation after checking the repository; this design does not invent a revision ID.
- Old revisions are preserved verbatim in a documented archive outside the active Alembic script location. The archive is evidence, not an importable second graph and not a source for fresh install.

### Version table contract

- Table: Alembic’s default `alembic_version`; no custom table name is proposed.
- Clean install: Alembic creates/maintains the table and writes the active canonical revision; no `stamp` operation.
- Expected state: exactly one row containing the single current active head revision. Runtime’s existing single-head/current-revision guard remains in place.
- The archive’s 23 revision IDs are historical evidence only after rebase; they are not accepted as current revisions by the new active graph.
- No automatic stamp is allowed. A local database may only be associated with the canonical head after a separately approved full schema fingerprint and state-adoption plan proves exact equivalence; otherwise it must be migrated/copied through a designed bridge or remain on a preserved backup.

## 5. Treatment of all ten discrepancies

See [`MIGRATION_REPAIR_MATRIX.md`](MIGRATION_REPAIR_MATRIX.md) for the required per-discrepancy fields and risk/rollback treatment.

- H1–H2: archive the incompatible/contradictory workspace operations, including the conditional `DATETIME` creation, duplicate `fcbc1a52044c` creator, and `b05fd7d45c87` deletion of `ws-demo` when owner is null. The canonical baseline creates the final workspace table once and deletes no data.
- H3–H9: create the seven missing ORM tables in the baseline in FK dependency order. Their target fields are already defined by the ORM/runtime inventory.
- H10: bypass the conditional partial creators (`0001_persistence` and `c13a7e91d204`) for clean install. The baseline creates complete definitions. Existing partial schemas use the local adoption gates, not baseline assumptions.

All ten are migration-history debt or migration-produced schema gaps, not open decisions about the target schema. No discrepancy warrants an in-place data deletion or a seed inside Alembic.

## 6. Seven missing table creators

All seven belong in the canonical baseline, not in historical revisions and not in post-baseline feature migrations:

1. `projects` after workspaces.
2. `datasets` after projects.
3. `workflows` after projects.
4. `workflow_versions` after workflows.
5. `workflow_executions` after workflows and before approvals/traces/provenance dependents.
6. `execution_traces` after executions.
7. `capability_execution_traces` after workflow executions.

The exact FK dependency order must be generated from the reconciled schema inventory during implementation. The baseline must not import ORM metadata to call `create_all()` and must not create data rows.

## 7. Workspace history treatment

- Keep `7757af5afe0a`, `fcbc1a52044c`, and `b05fd7d45c87` unchanged in the historical archive.
- Do not execute them in the new clean-install lineage.
- New empty PostgreSQL 16 installation reaches workspace schema through the canonical baseline only, using the ORM-defined timezone-aware timestamp type, one table creation, and required non-null owner contract.
- The baseline does not create `ws-demo`, delete any workspace, or infer/backfill an owner.
- Existing local DBs with `ws-demo`, null owners, or workspace structures from either historical creator are never auto-routed through the baseline. Inspect and back up first; preserving or transforming each record is an explicit local adoption/data-migration decision.
- A local DB on an old revision cannot safely follow the new lineage by `upgrade head` because the old revision IDs are no longer active. No existing local database can be declared safe to hand off without inspection and schema fingerprinting.

## 8. Existing local database path

No local DB is assumed disposable based on its filename or engine. The decision table below defines permitted handling; all write operations still require separate authorization.

| Category | Automatic migration allowed? | Backup required? | Schema inspection? | Reprovision preference | Stamp allowed? | Data migration? |
|---|---|---|---|---|---|---|
| **1. EMPTY / DISPOSABLE** — verified empty and explicitly classified | No startup automation. An explicitly authorized migration job may build the new baseline after re-verifying emptiness. | No data backup if emptiness/disposability is proven; preserve verification infrastructure as directed. | Yes: verify engine/version, no application tables/data, and no unexpected `alembic_version`. | Yes; fresh canonical baseline is preferred. | No. Use `upgrade head`. | No. |
| **2. CURRENT LOCAL DB** — currently used developer DB or old repository head | No. Explicit inspect/backup/adoption only. | Yes, before any schema/data write. | Yes, full schema, revision, and data ownership inventory. | Only if owner confirms data can be reconstructed; otherwise preserve/adopt. | Only after exact full fingerprint and explicit approval; default is no. | Conditional; preserve data and artifacts. |
| **3. HISTORICAL LOCAL DB** — older Alembic revision or metadata-created schema | No. | Yes, before any write or transfer. | Yes, including model-vs-schema differences and data dependencies. | Preferred only after data is classified and export/recreation is approved. | Normally no; only a proven exact fingerprint under an explicit adoption procedure. | Likely/conditional; design a version-specific bridge or export/import. |
| **4. UNKNOWN / MUST INSPECT** — provenance, contents, or version unclear | No; stop before write. | Make a protected backup before any authorized operation that can alter it. | Yes, read-only first. | Not until owner classifies data and retention need. | No. | Unknown; decide only after inspection. |

This applies to the tracked `data_quality.db`, any `postgres_data` Compose volume, and `aeop-postgres16-verify`. The owner says the latter is disposable validation infrastructure that must remain available; this does not permit deleting or migrating it in this design phase. SQLite `create_all()` schemas are not PostgreSQL baselines.

## 9. Alembic upgrade, stamping, and downgrade policy

- **Upgrade:** a dedicated serialized migration job only. New empty DBs use `alembic upgrade head` against the new active graph. Application/API/worker startup never runs Alembic or `create_all()` in production.
- **Existing local DB upgrade:** automatic `upgrade head` is prohibited until a separate compatibility/adoption plan recognizes the old revision and proves the schema/data path. The new graph will not silently interpret old revision numbers.
- **Stamping:** prohibited for clean installs, unknown DBs, and any schema produced only by `create_all()` without exact structural equivalence. Exceptional stamp-based handoff requires a protected backup, full fingerprint including all columns/types/nullability/defaults/indexes/unique/FKs/sequences, known data state, explicit owner approval, and a documented revision mapping. A partial comparison is not sufficient.
- **Downgrade:** unsupported for the canonical production path by default. Prefer forward-fix migrations. Application release rollback requires a database schema it can recognize; after the new baseline head, old application versions may reject the new revision under their exact-head check. Therefore rollback is either a tested compatibility release or restoration of a matching database backup/snapshot. Do not assume Alembic downgrade can recover `ws-demo` or other deleted local data.
- **Fresh disposable rollback:** after explicit authorization and proof that the DB is empty/disposable, discard/recreate may be used operationally; no such action is authorized here.

## 10. Fresh-install path

1. Provision a new isolated PostgreSQL 16 database with controlled owner/grants.
2. Verify empty state and record PostgreSQL version and database identity without application startup.
3. Run the dedicated migration job once; baseline and any linear descendants create the canonical schema. No local object, SQLite file, or external schema is consulted.
4. Validate exactly one active Alembic head and one matching `alembic_version` row.
5. Compare schema fingerprint to the canonical contract: all tables, columns, types, nullability, PKs, unique constraints, indexes, 43 FK actions, identity/sequence behavior, no unintended server defaults, and no demo/admin/business rows.
6. Run the separate idempotent RBAC reference seed (roles, permissions, role-permission links); it creates no user, admin credentials, organization, membership, or demo data.
7. Complete secure first-user/organization/membership onboarding through the separately approved operational flow.
8. Start API/application, validate the existing revision guard and representative persistence operations, then start workers.
9. Repeat `upgrade head` as a no-op verification in the validation environment; it must not change the schema fingerprint or seed state.

## 11. Existing-local adoption path

1. Stop automatic writes/migrations; identify engine, file/volume owner, Alembic revision if any, `create_all()` history, and data/artifact dependencies.
2. Preserve a backup/snapshot before any modification. For `data_quality.db` and `postgres_data`, do not recreate or prune during discovery.
3. Compare the local schema to the canonical fingerprint and identify data requiring retention.
4. If the database is empty and owner-classified disposable, use the clean-install path.
5. If data exists, prefer a new canonical database plus explicit export/import/transform with row counts, foreign-key/integrity validation, and rollback to the untouched source. This import path requires its own design and authorization.
6. Allow stamp-based handoff only for a proven exact schema and data-compatible state; never stamp merely because the revision is old or the ORM can query it.
7. If a state is unsupported or cannot be fingerprinted, leave it untouched and report blocked; do not force it into the new graph.

## 12. Rollback and restore model

- Baseline or migration-job failure on a verified empty disposable database: do not start the app; preserve logs, then clean/recreate only under separate disposable-resource authorization.
- Any migration/adoption involving local data: restore the pre-change full database backup (and related file/object-storage backup) rather than running speculative downgrades.
- New-head DB plus old app binary is not assumed compatible. The old runtime’s exact current-head guard can reject the new head. Rollback requires restoring the paired old DB snapshot or shipping a separately tested compatibility application release.
- No production baseline exists, but local rollback protection remains mandatory.

## 13. PostgreSQL 16 validation requirements

This plan is defined but not executed. Separate authorization is required before using `aeop-postgres16-verify` or any other database.

- Pin PostgreSQL major version 16 and the SQLAlchemy/Alembic dependency lock used for validation.
- Verify blank-database baseline succeeds without SQLite, `create_all()`, or pre-existing tables.
- Verify one root, one head, one `alembic_version` row; rerun upgrade and confirm no-op schema fingerprint.
- Inspect all 31 tables and compare columns/types/nullability, 43 `NO ACTION` FKs, indexes, unique constraints, three integer identity/sequence keys, and the absence of all seven persistent server defaults.
- Verify no `ws-demo` deletion or seed data is performed by schema migrations; run and repeat the separate RBAC seed in an isolated fixture after schema validation.
- Validate API and worker startup only after migrations and schema validation; confirm startup does not call `create_all()` or Alembic.
- Test representative CRUD/use cases, uniqueness/FK rejection, transaction behavior, audit/lineage/history retention, and default behavior. Add explicit tests for the seven direct-SQL default changes and no-cascade outcomes.
- Record the exact PG16 version, migration head, schema fingerprint, seed fingerprint, logs, and rollback evidence. Do not infer any result from SQLite.

## 14. Exact implementation boundary

If separately authorized, the repair implementation is limited to the active Alembic graph/baseline, preserving the 23 old migration files as an archive, migration-specific tests, and operator/design documentation. It must not change application models, runtime startup to migrate, Docker behavior, or data seed policy. Any need to alter those boundaries stops implementation for a new review.

No migration, archive move, stamp, database, source code, model, test, or runtime configuration changed in this design phase.

## 15. Risks and stop conditions

- **Legacy local DB version IDs become unrecognized by the new active lineage.** Stop and preserve until a state-specific adoption bridge is approved.
- **Local data may exist despite no production data.** Stop before any destructive/reprovision step until ownership, backup, and retention are explicit.
- **The baseline could diverge from the 31-table target.** Stop if any schema fingerprint item differs or is undocumented.
- **System seed could accidentally create an administrator or demo tenant.** Stop if seed output includes identity/tenant/business records or is not idempotent.
- **Multiple active heads could reappear through archived files or future branches.** Stop if the active Alembic script directory resolves to anything other than one head.
- **Application rollback against new head may fail exact revision validation.** Do not promise rollback without compatible app release or matching DB restore.
- **PostgreSQL 16 validation is unavailable or fails.** No implementation/deployment gate passes on SQLite-only evidence.

## 16. Authorization and next gate

The selected design does not authorize migration work. The next gate is explicit, separate authorization for (A) Alembic repair implementation and (B) isolated PostgreSQL 16 validation. Both requests must name their bounded scope; approval of one does not imply approval of the other.

```text
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
NEXT_GATE = Obtain explicit authorization for Alembic migration repair implementation and separate explicit authorization for isolated PostgreSQL 16 validation.
```

CANONICAL_TARGET_SCHEMA = DEFINED
MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB
MIGRATION_GRAPH_STATUS = REPAIR_DESIGN_COMPLETE
SELECTED_REPAIR_STRATEGY = D
ALEMBIC_HEAD_COUNT_DESIGN = 1
FRESH_INSTALL_PATH = DEFINED
EXISTING_LOCAL_DB_PATH = DEFINED
POSTGRESQL_16_VALIDATION_PLAN = DEFINED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
NEXT_GATE = Obtain explicit authorization for the Alembic repair implementation and separate explicit authorization for isolated PostgreSQL 16 validation.
