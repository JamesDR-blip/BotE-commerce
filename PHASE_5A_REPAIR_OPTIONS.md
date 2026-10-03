# Phase 5A — Alembic Repair Options

**Date:** 2026-10-02  
**Status:** design comparison only. No repair is selected, authorized, or implemented.

## Repair Objective

Establish a reproducible PostgreSQL 16 schema from a historically correct baseline, migrate existing production data without loss, and make new-environment provisioning deterministic. The immediate empty-database error (`DATETIME` in `7757af5afe0a`) is not the whole problem: the history also lacks creators for `datasets` and other ORM tables, and it contains a later unconditional workspace creator following the ownership revision.

The production baseline is **UNKNOWN**. The current disposable PostgreSQL verification database is empty and has no Alembic revision. It is not a substitute for the authoritative production schema.

## Strategy A — Repair Existing Migration Files In Place

**What changes:** Amend the raw workspace type/DDL and potentially alter ordering/guards or table operations in historical revisions so the chain passes from an empty database.

| Impact | Assessment |
|---|---|
| Existing production databases | If any affected revision was already applied, its stored Alembic version will not cause the amended body to rerun; fresh installations would execute changed historical semantics. Existing and new environments could diverge. |
| Fresh PostgreSQL database | Could fix the first `DATETIME` parse error, but does not by itself add missing dataset/workflow baseline tables or resolve duplicate workspace creation. |
| Alembic revisions | Revision IDs remain but published migration behavior changes; operator expectations and reproducibility change. |
| Downgrade | Existing downgrade code would need independent review; historical revisions may be irreversible or data destructive. |
| Data-loss risk | High if guards/cleanup or inferred schema are added without knowing actual data shapes; `b05` already deletes a row and integrity revisions rewrite hashes. |
| Production risk | High. Same revision identifier can denote different DDL in different deployed code versions. |
| Compatibility risk | High across databases already at any intermediate revision. |
| Requires authoritative baseline? | **Yes.** Not safe without determining deployed revisions and object/data states. |

**Assessment:** Not authorized. A one-line type fix would be insufficient and could give false confidence.

## Strategy B — Add a New PostgreSQL / Bootstrap Migration Path

**What changes:** Add an explicit fresh-database preparation or alternate baseline/provisioning path while retaining existing upgrade revisions.

| Impact | Assessment |
|---|---|
| Existing production databases | Must detect/adopt current schemas without recreating objects or replaying incompatible history. Multiple starting states need explicit routing. |
| Fresh PostgreSQL database | A bootstrap step could create a known baseline, but the current linear upgrade path still encounters old revisions unless the path establishes a valid starting revision/branch; a bootstrap that merely precreates tables risks duplicate DDL. |
| Alembic revisions | May introduce a new branch/head, explicit baseline revision, or external provisioning boundary; head and merge semantics must be designed. |
| Downgrade | Fresh bootstrap rollback could drop substantial data; existing baseline adoption cannot safely be reversed by generic downgrade. |
| Data-loss risk | High if bootstrap objects or baseline state are inferred from ORM metadata. |
| Production risk | High until start-state detection and upgrade paths are rehearsed. |
| Compatibility risk | Medium/high due multiple supported installation paths and revision graph complexity. |
| Requires authoritative baseline? | **Yes.** At minimum, the exact intended clean-install schema and production-compatible revision must be established. |

**Assessment:** Not authorized. It cannot be treated as a shortcut around missing history.

## Strategy C — Explicit Baseline / Provisioning Migration, Preserve Existing Production History

**What changes:** After identifying the true baseline, define a deterministic fresh-install baseline/provisioning artifact and a controlled transition into the preserved forward migration history. Existing installations retain their recorded revisions and data; new installations begin from the explicit baseline contract.

| Impact | Assessment |
|---|---|
| Existing production databases | Potentially lowest historical disruption if the baseline matches actual production and current revisions are verified; adoption/takeover still requires an explicit non-destructive procedure. |
| Fresh PostgreSQL database | Can become deterministic if the baseline is complete, PostgreSQL 16-tested, and its handoff revision corresponds exactly to the first subsequent migration. |
| Alembic revisions | Existing revisions can remain immutable; a fresh-install path or baseline revision/branch and merge strategy must be proven against Alembic graph rules. |
| Downgrade | Baseline teardown is potentially destructive; do not represent it as a routine downgrade. Document forward recovery and restore. |
| Data-loss risk | Medium after evidence and rehearsal; currently high because baseline contents and row requirements are unknown. |
| Production risk | Medium after per-state rehearsal and backup/restore; currently high. |
| Compatibility risk | Medium; all supported existing revision states and fresh path must converge to the same schema. |
| Requires authoritative baseline? | **Yes, absolutely.** |

**Assessment:** This is a candidate for future evaluation because it can preserve existing revision history, but it is **not selected** and cannot be designed concretely until authoritative baseline evidence is obtained. Do not stamp or mark any database during this phase.

## Strategy D — Rebuild / Replace the Migration Chain

**What changes:** Replace or squash the current history with a new baseline and subsequent migrations.

| Impact | Assessment |
|---|---|
| Existing production databases | Requires mapping every deployed revision/schema to a new lineage and a controlled adoption procedure; existing Alembic state may no longer match. |
| Fresh PostgreSQL database | Could be clean if rebuilt from verified DDL and tested, but that DDL is not currently known. |
| Alembic revisions | Rewrites identity/history and likely creates a new baseline/branch; all deployment environments need coordinated adoption. |
| Downgrade | No meaningful generic downgrade across a history replacement; recovery depends on backups and forward fixes. |
| Data-loss risk | Very high without authoritative inventory and rehearsed transform; high even with a baseline due cross-version adoption. |
| Production risk | Very high; broad operational migration. |
| Compatibility risk | Very high across installations and operators. |
| Requires authoritative baseline? | **Yes, plus inventory of every deployed revision/state.** |

**Assessment:** Highest disruption. Not justified by the present evidence.

## Comparison Matrix

| Criterion | A: edit existing revisions | B: new bootstrap path | C: explicit baseline, preserve history | D: rebuild history |
|---|---|---|---|---|
| Preserves existing revision bodies | No | Usually | Yes, as design goal | No |
| Could support deterministic fresh PG16 install | Possibly, after broader corrections | Possibly, with graph/start-state design | Yes, if baseline and handoff are proven | Yes, if rebuilt from authoritative schema |
| Existing deployments remain distinguishable | Weakly; same IDs change meaning | Yes, but multiple paths | Yes; baseline and existing histories remain explicit | Difficult |
| Current production data safety | Unknown/high risk | Unknown/high risk | Best potential only after baseline verification | Highest risk |
| Handles missing datasets/workflow tables | Requires more historical edits | Requires explicit baseline setup | Baseline can define them, subject to evidence | Can redefine all, subject to evidence |
| Resolves workspace duplication | Requires editing old history | Must guard/route baseline | Can preserve old revisions and avoid duplicate on fresh path if handoff proven | Rebuilds, but adoption complex |
| Requires authoritative production evidence | Yes | Yes | Yes | Yes |
| Current authorization | Not authorized | Not authorized | Not authorized | Not authorized |

No option is safe to implement based on the empty disposable database alone. The database confirms the first failure environment and empty state; it contains no historical production objects or data from which a baseline can be reconstructed.

## Production Safety Analysis

Production schema state, applied revision, and prior provisioning method remain unknown. The repository has a targeted destructive `DELETE` in `b05fd7d45c87`; later revisions backfill integrity hashes and change nullability. Historical edits can also create different semantics for databases that already applied a revision. No production repair, stamp, downgrade, or upgrade is authorized.

Before any production repair design can be approved, obtain the authoritative schema-only PostgreSQL 16 artifact, exact Alembic state, environment provenance, required extensions, and operator provisioning/startup sequence. Compare without inferring missing objects from ORM models. Define a separate disposable database per tested starting state and prove the proposed path before touching a shared or production system.

## Fresh-Database Safety Analysis

The current empty-database path is **FAIL**. The observed first PostgreSQL 16 error is invalid raw `DATETIME`; after that is addressed, the current chain still contains missing baseline objects and an unconditional duplicate workspace creator. A type-only change, `create_all()` substitution, `stamp`, or precreation from current ORM metadata would not prove a correct baseline and is not recommended.

## Data Preservation Analysis

- `b05fd7d45c87` deletes `workspaces.id='ws-demo'` only when `owner_id IS NULL`; downgrade does not restore it.
- `20260926_01` calculates and persists `integrity_hash` for existing changeset rows and then requires a value.
- `20260928_01` recalculates hashes including ordered item snapshots; downgrade recalculates base changeset hashes.
- Workspace ownership, user references, dataset references, approvals, audit/lineage rows, and changeset snapshots may have production data/constraints not represented in the disposable empty database.
- A restore-tested backup and row-level preservation checks are mandatory before applying any eventual repair to an existing database.

## Recommended NEXT INVESTIGATION

Request **one authoritative PostgreSQL 16 schema-only dump from the production owner**, accompanied by the dump timestamp/environment identity, provisioning method, required extensions, and the source environment's Alembic revision. Do not request credentials or application row data. If a dump cannot be provided, the equivalent next artifact is an explicitly approved isolated staging database known to match production, with read-only inspection authorization.

This request is evidence acquisition only. It does not authorize connecting to production, changing revisions, stamping, or migration execution.

## Preconditions for Actual Repair

1. Authoritative production schema and exact applied revision are verified, not inferred.
2. Every supported deployed starting revision/state is inventoried; no hidden/second history is assumed away.
3. Tables, columns, indexes, constraints, foreign keys, schemas, extensions, enum/types, defaults, ownership/grants, and relevant seed/reference rows are compared to repository requirements.
4. The authoritative baseline's provisioning history is known, including whether/how ORM `create_all()` participated.
5. The workspace timeline, duplicate creation, dataset/workflow model-only baseline, user branch, and destructive/backfill data effects have explicit decisions.
6. A selected repair has separate proof for empty PostgreSQL 16 provisioning and upgrade from every supported authoritative existing state.
7. A database backup is restored into an isolated database; schema/revision and representative reads/writes are checked.
8. API and worker startup, representative dataset/quality/workflow persistence, audit/trace, and required Redis-backed worker flow pass against the repaired disposable schema.
9. Downgrade limitations, recovery path, deployment ordering, monitoring, and operator approval are documented.
10. Explicit authorization for migration repair is obtained in a later phase. Nothing here grants that authorization.

## Explicit NO-GO Conditions

- `PRODUCTION_SCHEMA_BASELINE = UNKNOWN`.
- PostgreSQL runtime evidence limited to an empty disposable database.
- Production/staging Alembic revision remains unknown.
- Baseline upgrade, API/worker runtime, representative persistence, and backup/restore remain unverified.
- Migration chain contains the confirmed `DATETIME` PG failure and workspace duplicate/missing-object assumptions.
- Any strategy requires guessing at historical schema from ORM metadata or SQLite.
- No migration repair, Alembic stamp, downgrade, production connection, or deployment action is authorized by Phase 5A.

**Current status:** `REPAIR_AUTHORIZATION=NOT_AUTHORIZED`; `PHASE_5A=INCOMPLETE`; `PHASE_5=NO-GO`.
