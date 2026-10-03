# First Production Migration Options

**Date:** 2026-10-02  
**Status:** design comparison only; no strategy selected and no implementation authorized.

## Decision context

The project owner confirms there has never been a production or staging deployment, production database, or production data. PostgreSQL 16 is the intended production engine. The task is therefore to provision a first production database, not to take over a historical production schema.

That fact removes production-data preservation as a constraint. It does not establish the desired schema contract, prove that local development databases are disposable, or make the present Alembic chain a valid empty PostgreSQL bootstrap. The current ORM metadata lists 31 tables, but it is only an input to schema review. See [FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md](FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md) for table inventory and revision evidence.

The current repository head is `20260928_01`. The inspected chain fails on PostgreSQL 16 at `7757af5afe0a` because the migration uses raw `DATETIME`; subsequent revisions also assume tables that no earlier revision creates. There is a later unconditional workspace creator, conditional/branch-dependent DDL, data backfills, and a deletion of `ws-demo`. A successful fix must address the whole selected path, not just the first error.

## Option A — repair the existing chain in place

**Description:** Edit existing revisions so the current chain provisions the approved schema from an empty PostgreSQL 16 database through `20260928_01`.

**Advantages**

- Preserves one familiar Alembic lineage and the current production startup check for the repository head.
- Keeps the deployment migration command and version table model comparatively simple.
- Avoids introducing a second script location or migration graph.

**Risks and required design work**

- Changes the historical behavior of revisions that may already have been applied to local/development databases. Alembic will not re-run edited revisions already recorded in `alembic_version`, so those databases could silently differ from a fresh installation.
- Must reconcile the complete chain: PostgreSQL-compatible types, missing base tables and their dependency order, conflicting workspace creation, conditional DDL, data-dependent backfills, seed assumptions, and destructive `ws-demo` cleanup.
- Downgrade behavior and data restoration need explicit review; some current downgrades are no-ops or cannot restore deleted data.
- Before this option can be considered, inventory every supported local database revision/state and decide whether those states are upgradeable, disposable, or require a separate transition.

**Risk:** High until local/development database states and the canonical schema contract are known.  
**Rollback:** Reverting source-control edits does not undo an already-run migration. Any implementation would need a reviewed database recovery plan before execution; no downgrade should be assumed safe.  
**Assessment:** Not currently selected or authorized.

## Option B — preserve the old history and establish a clean-install lineage

**Description:** Keep existing migration files unchanged as historical evidence and design a separate, explicit Alembic path for a fresh installation. The new path would provision one approved baseline and then apply only its compatible forward revisions.

**Advantages**

- Does not rewrite the recorded meaning of the existing historical revisions.
- Can make empty PostgreSQL 16 provisioning deterministic once the target schema is approved.
- Makes the distinction between legacy/local database history and fresh installation explicit.

**Risks and required design work**

- A second root or branch in the current script location can create multiple Alembic heads. That is incompatible with current production wiring that expects a single repository head unless the graph and runtime revision check are deliberately redesigned.
- A merge revision alone does not solve the problem if it still depends on the broken legacy chain; Alembic would execute the failing legacy revisions first.
- The active script location, version-table treatment, revision identity, deployment command, and startup head check need one coherent design. Do not stamp an empty database or claim it is upgraded.
- Existing local databases on the old chain need an explicit compatibility path. Preserving old files does not automatically make old database states compatible with the new baseline.
- Seed data and defaults must be specified rather than copied implicitly from ORM metadata or SQLite fixtures.

**Risk:** Medium to high until the graph/runtime integration and local database-state inventory are designed.  
**Rollback:** Before rollout, revert the new migration path and wiring. After any database has used it, recovery requires a separately rehearsed restore/reprovision procedure; do not assume downgrade or version-table edits are safe.  
**Assessment:** Plausible design direction, not selected or authorized.

## Option C — external schema artifact followed by Alembic handoff

**Description:** Provision an approved schema artifact (for example, reviewed PostgreSQL DDL or an immutable schema-only artifact) through a dedicated provisioning step, then have Alembic manage later revisions from an explicitly defined baseline revision.

**Advantages**

- Can separate initial schema creation from later incremental changes where an established infrastructure provisioning system already owns DDL.
- Could be useful if the organization has an authoritative, versioned provisioning artifact and clear ownership for applying and testing it.

**Risks and required design work**

- No authoritative provisioning artifact or deployment system is evidenced in the repository or supplied project facts. Creating one now would be a new source of schema truth, not reuse of an existing authority.
- The artifact and Alembic must share an exact schema fingerprint and an explicit handoff revision. A mismatch leaves Alembic unable to safely reason about the database.
- This creates two provisioning mechanisms to test and operate, and may duplicate DDL or seed policy.
- Stamping or manually marking a database at a revision is explicitly out of scope and cannot substitute for proving the artifact-to-revision handoff.

**Risk:** High without an existing authoritative artifact and owner.  
**Rollback:** Reprovision a disposable database from the prior pinned artifact and restore application data only through a separately verified backup process; do not use destructive rollback on a live database.  
**Assessment:** Not evidence-supported at present; reject unless an authoritative artifact and its operational owner are produced.

## Comparison

| Criterion | Option A: edit current chain | Option B: separate clean-install lineage | Option C: external artifact handoff |
|---|---|---|---|
| Leaves historical revision contents intact | No | Yes | Yes, if old chain retained |
| Can be made to bootstrap empty PostgreSQL 16 | Yes, after full-chain repair | Yes, after explicit graph/runtime design | Yes, if artifact and handoff are proven |
| Preserves current single-head runtime assumption directly | Most likely, after repair | No; must deliberately preserve or revise it | Depends on handoff design |
| Requires canonical target schema approval | Yes | Yes | Yes |
| Requires local/development state inventory | Yes | Yes | Yes |
| Repository evidence supports its prerequisite today | Partially; existing chain is present but state compatibility is unknown | Partially; Alembic is present but new graph design is absent | No authoritative artifact found |
| Assessment status | Not selected | Not selected | Not supported by current evidence |

## Recommendation and decision

**Migration strategy remains `UNDECIDED`.** The current evidence is insufficient to select A or B safely: the canonical target schema is not approved, and supported local/development database states have not been inventoried. Option C lacks an evidenced authoritative artifact and owner.

The next design inputs are:

1. Approve a PostgreSQL 16 schema contract by reconciling ORM declarations with repository/domain behavior, including `users.email` uniqueness, defaults, constraints, seed/reference data, and audit/ChangeSet invariants.
2. Inventory local/development databases and the Alembic revisions they record; state which must remain usable and how each would transition.
3. Select one Alembic graph/runtime model, including active script location, one-head policy, version-table semantics, API/worker startup checks, and deployment migration-job ordering.
4. Design and review first-install, application-startup, worker-startup, representative operation, and restore tests against isolated PostgreSQL 16.

No option in this document authorizes implementation, database provisioning, Alembic execution, stamping, or production use.

```text
FIRST_PRODUCTION_PROVISIONING = REPAIR_DESIGN_BLOCKED
CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
MIGRATION_STRATEGY = UNDECIDED
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```
