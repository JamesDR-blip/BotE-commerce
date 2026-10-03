# First Production Migration Strategy Comparison

**Date:** 2026-10-02  
**Status:** compare only; no option selected.  
**Input:** [CANONICAL_SCHEMA_RECONCILIATION.md](CANONICAL_SCHEMA_RECONCILIATION.md).

## Context

There is no historical production database or production data to preserve. The objective is first production provisioning on PostgreSQL 16. The canonical target schema remains undefined because current ORM metadata, historical Alembic DDL, application runtime contracts, and tests do not fully agree or prove PostgreSQL behavior.

Current evidence: 31 ORM tables; 23 connected Alembic revisions ending at `20260928_01`; the current chain fails for empty PostgreSQL at the recorded raw `DATETIME` operation in `7757af5afe0a`; multiple table creators are absent; workspace creation is duplicated; and some revisions perform data-dependent or destructive operations. No database, migration, test, or container operation was performed for this comparison.

## Option A — repair the existing 23-revision chain

Edit existing revisions so the declared history, starting at its root, creates the approved PostgreSQL 16 schema and advances to the existing head.

| Concern | Assessment |
|---|---|
| Reproducibility | Could be reproducible after every revision and conditional branch is reconciled and tested. |
| Clean install | Requires fixing the initial PostgreSQL type error, adding missing base schema at the correct point, resolving duplicate workspace creation, and addressing all FK prerequisites. Fixing only the first error is insufficient. |
| Existing-database behavior | Editing a revision does not re-run it on databases already stamped at that revision. Fresh and existing local databases could then have divergent schemas under identical revision IDs. Their supported states are unknown. |
| Alembic semantics | Retains the existing root/head identifiers and likely the simplest one-head runtime check, but rewrites the meaning of historical revision IDs. |
| Future upgrade safety | Requires proving every supported local starting revision/state can reach the same target and documenting edited historical semantics. |
| Rollback | Source revert cannot undo an already-applied DDL/data migration. Current downgrades include no-ops, dropped state, or data that cannot be reconstructed. Restore/reprovision plans are required. |
| Data migration | Must separately decide whether to retain or omit `ws-demo` deletion and how to handle hash backfills/recalculation. |
| Operator complexity | Lower graph complexity, higher legacy-state compatibility burden. |
| Testability | Can test a single chain from empty and each supported existing local revision, but the current evidence has no PG matrix. |
| Application compatibility | Must match all current ORM/repository and application contracts; currently not proven. |
| Silent semantic change risk | High: same revision IDs can produce different results depending on when they were applied. |

## Option B — preserve old history and introduce a clean-install lineage

Retain existing revisions as historical evidence while designing a distinct Alembic path for new installations, with a controlled strategy for existing local databases.

| Concern | Assessment |
|---|---|
| Reproducibility | Potentially strong for new installs once one target baseline and one subsequent forward path are pinned. |
| Clean install | Can start from a complete approved PostgreSQL baseline, but only if the selected active lineage does not execute the broken old path first. |
| Existing-database behavior | Requires explicit handling for old local databases at every supported revision. No local state inventory exists yet. |
| Alembic semantics | A second root in the same script location may create multiple heads. Current startup calls `get_current_head()` and expects one head. Script location, head policy, version-table semantics, deployment command, and startup check would need one coherent design. A merge revision alone does not skip or repair earlier prerequisites. |
| Future upgrade safety | Good only if fresh and existing paths converge to the same schema fingerprint and future revisions have one unambiguous parent/history policy. |
| Rollback | A new lineage can be reverted before use; after databases adopt it, restore/reprovision is required unless specific downgrade behavior is proven. Do not stamp a database to claim adoption. |
| Data migration | Fresh install needs no production data transform; local existing installations may need explicit transition/backfill treatment. |
| Operator complexity | Higher: operators need to select and support fresh versus existing paths, unless the graph/runtime design eliminates that distinction. |
| Testability | Requires tests for empty install, each supported old local state, single-head checks, API/worker startup, and convergence. |
| Application compatibility | Must provision the same runtime schema consumed by current code; no source behavior change is implied, but schema/runtime parity must be tested. |
| Silent semantic change risk | Lower for preserved revision bodies, but high if the baseline artifact or version handoff is guessed. |

## Option C — explicit schema artifact followed by Alembic handoff

Use a separately versioned PostgreSQL DDL/schema artifact to provision the baseline, followed by Alembic revisions from an explicitly defined handoff point. No such authoritative artifact or deployment owner is currently evidenced.

| Concern | Assessment |
|---|---|
| Reproducibility | Possible if the artifact is immutable, reviewed, PostgreSQL-tested, and has a matching Alembic handoff. |
| Clean install | The artifact could provision empty PostgreSQL 16, but the current Alembic chain must still be bypassed or explicitly bridged without pretending it ran. |
| Existing-database behavior | Each existing local state must be reconciled to the artifact/handoff; no generic stamping or inferred adoption is acceptable. |
| Alembic semantics | Creates an artifact-to-version contract in addition to migration graph semantics. A schema fingerprint and explicit ownership boundary are mandatory. |
| Future upgrade safety | Depends on keeping artifact and Alembic baseline exactly synchronized; duplicate sources can drift. |
| Rollback | Reprovision disposable environments from the previous pinned artifact. Existing data recovery requires separately verified backup/restore. |
| Data migration | No production data transform is required for first install; local data transition remains open. |
| Operator complexity | Highest unless infrastructure already owns a versioned schema artifact; repository evidence does not show one. |
| Testability | Requires artifact application, schema fingerprint, Alembic handoff, runtime operations, and artifact/Alembic drift checks. |
| Application compatibility | Must match current runtime needs and schema acceptance gates. |
| Silent semantic change risk | High while the artifact and owner are invented; lower only after governance is established. |

## Comparison summary

| Criterion | A: edit current chain | B: new clean-install lineage | C: artifact handoff |
|---|---|---|---|
| Preserve old revision bodies | No | Yes | Yes, if history remains archived/available |
| Fresh PostgreSQL 16 path | Possible after full-chain repair | Possible after graph/runtime design | Possible after artifact/handoff design |
| Existing local DB handling | Required; unknown | Required; unknown | Required; unknown |
| Single-head startup compatibility | Likely easiest, still must verify | Must explicitly design | Must explicitly design |
| Need approved target schema | Yes | Yes | Yes |
| Evidence prerequisite exists now | Partial | Partial | No artifact/owner evidenced |
| Strategy selected | No | No | No |

## Decision and next gate

**`MIGRATION_STRATEGY = UNDECIDED`.** No option wins on present evidence. In particular, absence of production data does not justify selecting or altering a chain before local database compatibility, target schema semantics, and Alembic runtime behavior are understood.

Before implementation authorization:

1. Resolve the schema decisions enumerated in [CANONICAL_SCHEMA_RECONCILIATION.md](CANONICAL_SCHEMA_RECONCILIATION.md), including email uniqueness, defaults, PostgreSQL types, FK/delete behavior, seed rows, and integrity/hash contracts.
2. Inventory supported local/development databases and their Alembic revisions; document which are disposable and which need a transition.
3. Select one lineage/version-table/startup-check/deployment-job design and prove that fresh and supported existing paths converge to the same canonical schema.
4. Define a non-destructive rollback and database restore/reprovision procedure for each supported starting state.
5. Approve a PostgreSQL 16 validation matrix covering empty install, supported upgrades, API and worker startup without `create_all()`, representative reads/writes, schema comparison, and backup/restore rehearsal.
6. Obtain explicit authorization in a later phase. This comparison authorizes no schema, migration, runtime, or deployment work.

```text
MIGRATION_STRATEGY_COMPARISON = COMPLETE
MIGRATION_STRATEGY = UNDECIDED
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```
