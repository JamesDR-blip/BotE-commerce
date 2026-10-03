# Final Canonical Schema Contract Review

**Review date:** 2026-10-02

**Scope:** read-only review of the six schema contracts and `SCHEMA_DECISION_REGISTER.md`. No source, ORM model, migration, test, Docker, or runtime file was changed. No Alembic command, database access, or test was performed.

**Status:** This review is a historical snapshot and is superseded by [`TARGET_SCHEMA_RECONCILIATION.md`](TARGET_SCHEMA_RECONCILIATION.md). The later reconciliation resolves the three FK candidates to `NO ACTION`, classifies the seven actual persistent server-default differences, and defines the logical target schema while leaving the Alembic graph in repair design.

## A. Confirmed canonical decisions

| Topic | Review result | Evidence / boundary |
|---|---|---|
| Deployment history | First-production provisioning; no prior production/staging database or production data exists. No historical production baseline needs preservation or reconstruction. | Owner decision recorded in `CANONICAL_SCHEMA_CONTRACT.md`; local developer data remains a separate preservation concern. |
| Schema inventory | The register and field inventories cover 31 ORM tables, 41 Python defaults, and 43 foreign keys. The default matrix contains 41 field rows; the FK matrix contains 43 individual rows, plus a separate repeated list of the three exception candidates. | Static document count only; no models were imported and no tests were run for this review. |
| Default ownership | All 41 Python defaults remain application-owned. Only database identity/sequence generation for integer autoincrement keys is database-owned. | Consistent with `APPLICATION_OWNED_UNLESS_DATABASE_INVARIANT`. Application-owned values are not converted to server defaults merely for normalization. |
| Default exception | `executions.status` keeps the application value `COMPLETED`; the historical migration's lowercase server default `completed` is excluded from the target. | This intentionally changes what a direct SQL insert that omits the value receives. No production state is affected, but local database state must be classified before any transition. |
| FK default | `NO ACTION` is the conservative target for all 43 relationships unless a specific CASCADE exception is confirmed. Nullable columns do not imply `SET NULL`; ORM `delete-orphan` is not itself a database cascade. | Consistent with the owner policy. The three candidate exceptions remain open below. |
| System seed | Only the persisted RBAC role, permission, and role-permission reference catalogue is identified as required system seed. It is separate from schema creation and must be provisioned before governed access is served. | The existing container configures persisted RBAC; empty persisted authorization records grant no permission. |
| Admin/demo data | No initial admin or credentials; no demo/sample records. User, organization, and membership onboarding is a separate operational action. | Consistent across the seed contract and owner policy. |
| Operations | Dedicated migration job is the selected model. API and worker startup must not run migrations or `create_all()`. | The current production container revision check is only a guard. The migration job is not yet implemented in deployment configuration. |
| Local state | Tracked SQLite state and persistent Compose volumes are preserved until inspected. The owner-designated PostgreSQL 16 verification container is to remain available. | No local database or volume was accessed during this review. |

### Cross-document consistency gaps

- `DATABASE_OPERATING_CONTRACT.md` specifies the migration sequence and startup restriction, but does not itself state PostgreSQL 16 as the target or explicitly state that no historical production baseline exists. Those facts appear in `CANONICAL_SCHEMA_CONTRACT.md`; repeating them in the operating contract would make it self-contained. This is an omission, not a conflicting policy.
- The earlier decision/status tables in `SCHEMA_DECISION_REGISTER.md` still say the default, FK, seed, and operating decisions are unresolved and show `MIGRATION_STRATEGY = UNDECIDED` / four decisions remaining. Its opening note and final owner-policy overlay explicitly supersede those entries and state the current result (three FK exceptions; dedicated migration job selected), so the latest status is identifiable, but the retained stale blocks are easy to misread and should be consolidated in a later documentation pass.
- The default matrix names the seven legacy server defaults being removed, but only `executions.status` is explicitly tagged as a direct-SQL runtime behavior exception. The other seven need the same exception status before implementation authorization.

### Default behavior changes that require explicit release notes/tests

The matrix explicitly identifies the `executions.status` casing exception. Seven more fields have persistent server defaults in historical migration files that the owner policy excludes from the canonical target: `compliance_policies.enabled`, `sync_attempts.external_product_id`, `risk_policies.high_risk_threshold`, `risk_policies.critical_risk_threshold`, `channel_mappings.external_product_id`, `channel_mappings.last_synced_hash`, and `channel_mappings.active`. Removing those defaults changes direct-SQL behavior when an insert omits the column. The current field matrix records the historical server defaults and their removal, but does not label these seven rows as runtime behavior exceptions. This is a documentation completeness gap to correct before implementation authorization. It does not change the owner decision that application defaults remain authoritative.

## B. Remaining owner decisions

The FK matrix has three `OWNER_DECISION_REQUIRED` candidates. Existing code does not establish that database CASCADE is needed for any of them; the review does not choose an action.

| Parent | Child FK | Why CASCADE was considered | Consequence of NO ACTION | Does repository/runtime behavior require DB CASCADE? | Status |
|---|---|---|---|---|---|
| `organizations` | `organization_quotas.organization_id` | Quotas are organization-owned configuration, and the ORM relationship uses `delete-orphan`. | A hard delete of an organization is rejected while quota rows reference it; an operator/use case would have to remove quota rows first or retain the organization. | **No evidence that it does.** There is no repository organization-delete operation or runtime path depending on DB-level cascade. ORM unit-of-work behavior is not proof of direct SQL behavior. | OWNER_DECISION_REQUIRED |
| `roles` | `role_permissions.role_id` | Role-permission rows are association children and the ORM relationship uses `delete-orphan`. | A hard delete of a role is rejected while links remain; links must be removed first or the role retained. | **No evidence that it does.** Persisted authorization reads the links, but no role-delete runtime path requires the database to remove them automatically. | OWNER_DECISION_REQUIRED |
| `permissions` | `role_permissions.permission_id` | Role-permission rows are association children and the ORM relationship uses `delete-orphan`. | A hard delete of a permission is rejected while any role link remains; links must be removed first or the permission retained. | **No evidence that it does.** The repository has create/link/read behavior; no permission-delete path establishes a database cascade requirement. | OWNER_DECISION_REQUIRED |

The safe default remains `NO ACTION` for all three until the owner explicitly confirms an exception. This is a policy default, not a decision that a cascade is required.

## C. Schema-history discrepancies

The supplied/repository evidence describes one connected history of 23 revisions. Its current head is documented as `20260928_01`. The empty PostgreSQL 16 bootstrap is known to fail, so this history is **not** a clean-install graph. For the requested discrepancy count, each issue below is counted once; the DATETIME and duplicate-create issues are distinct even though the workspace history overlaps.

| # | Discrepancy | Classification | Canonical impact |
|---:|---|---|---|
| 1 | Revision `7757af5afe0a` contains raw `DATETIME`, which is PostgreSQL 16-incompatible and is the known empty-bootstrap failure point. | LEGACY_MIGRATION_DEBT; clean-install path repair required. | Does not authorize changing the application timestamp contract; target DDL must use a PostgreSQL-supported type consistent with the reconciled model. |
| 2 | Workspace creation is contradictory: `7757af5afe0a` has a conditional creator and `fcbc1a52044c` later attempts an unconditional creator; subsequent revisions alter the table. | LEGACY_MIGRATION_DEBT; exact revision handling needs repair design. | The final workspace shape must follow the reconciled ORM/runtime contract; history cannot be run as-is from empty. |
| 3 | No migration creator evidence for `projects`. | LEGACY_MIGRATION_DEBT. | Required runtime table is absent from the current chain's creator evidence. |
| 4 | No migration creator evidence for `datasets`; `d14c1f2a9b31` alters it before a chain creator. | LEGACY_MIGRATION_DEBT. | Required runtime table and dependency order must be supplied by a reviewed clean-install design. |
| 5 | No migration creator evidence for `workflows`. | LEGACY_MIGRATION_DEBT. | Required runtime table is absent from creator evidence. |
| 6 | No migration creator evidence for `workflow_versions`. | LEGACY_MIGRATION_DEBT. | Required runtime table is absent from creator evidence. |
| 7 | No migration creator evidence for `workflow_executions`; a later revision alters it. | LEGACY_MIGRATION_DEBT. | Required runtime table must precede dependent revisions. |
| 8 | No migration creator evidence for `execution_traces`. | LEGACY_MIGRATION_DEBT. | Required persistence table is absent from creator evidence. |
| 9 | No migration creator evidence for `capability_execution_traces`. | LEGACY_MIGRATION_DEBT. | Required persistence table is absent from creator evidence. |
| 10 | Conditional legacy creators are partial-state dependent: `0001_persistence` conditionally creates related persistence tables based on table existence; `c13a7e91d204` conditionally creates `agent_memory`. These paths do not reconcile arbitrary partial schemas. | LEGACY_MIGRATION_DEBT; supported predecessor-state assumptions need explicit repair design. | They cannot be treated as a complete empty-install or general schema-reconciliation mechanism. |

**Count: 10 discrepancies** under the counting rule above. Their existence is explicitly classified as migration-history debt, not evidence of a historical production baseline. The current contracts do not yet provide a revision-by-revision repair design or prove the PostgreSQL 16 target DDL.

## D. Decisions intentionally deferred

- The three possible FK CASCADE exceptions remain owner decisions. `NO ACTION` remains the effective contract pending a decision.
- Alembic history repair, clean-install ordering, and single-head graph strategy remain design work. Do not infer permission to rewrite or squash revisions from this review.
- PostgreSQL-rendered DDL and runtime validation remain unverified. No SQLite result is substituted for PostgreSQL 16 evidence.
- Persistent local SQLite files and Compose volumes remain uninspected and must be preserved until separately classified. The absence of production data does not classify developer-local data as disposable.
- Exact migration job deployment, locks, database role/grants, credential delivery, backups, and restore process remain implementation prerequisites.
- The seven historical server-default removals are owner-directed, but their direct-SQL behavior change needs explicit per-field exception marking and regression coverage before implementation.

## E. Preconditions for implementation authorization

1. Resolve or explicitly retain the conservative `NO ACTION` outcome for each of the three FK candidates; update both matrices and the register so the pending count is unambiguous.
2. Mark all eight direct-SQL default behavior changes (the seven persistent historical server defaults plus `executions.status`) as exceptions in the field matrix. Preserve application-side default behavior for all 41 fields.
3. Reconcile the 31-table logical schema against ORM/runtime/migration evidence and record each of the 10 migration-history discrepancies as legacy migration debt or, if evidence shows otherwise, unresolved canonical ambiguity.
4. Prepare a clean-install Alembic graph repair design consistent with a single-head strategy and the dedicated migration job. Do not alter history until separately authorized.
5. Define PostgreSQL 16 schema validation and regression coverage for target DDL, defaults, FK actions, system seed idempotency, application/API startup, and worker startup. Keep the `aeop-postgres16-verify` environment isolated and use it only after explicit execution authorization.
6. Classify/preserve local persistent states before any operation that could touch them. Document job role/grants, secret handling, schema validation failure behavior, and backup/restore expectations.
7. Obtain explicit implementation authorization. This review itself grants none.

## F. Exact next gate

The next gate is a **documentation/design closure**: decide the three FK candidates (or retain `NO ACTION` for each), mark the seven legacy server-default removals as runtime exceptions, and complete the target-versus-history classification for all 10 discrepancies. Then re-review the canonical contract. Only after the contract is internally consistent and the clean-install repair design is approved may a separate request authorize implementation or PostgreSQL 16 validation. No migration repair or implementation is authorized by this report.

```text
CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
SCHEMA_DECISIONS_REMAINING = 3
SCHEMA_HISTORY_DISCREPANCIES = 10
MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB
MIGRATION_GRAPH_STATUS = REQUIRES_REPAIR_DESIGN
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
NEXT_GATE = Resolve the three FK cascade candidates, explicitly classify the seven legacy server-default behavior changes, and close the target-schema versus migration-history reconciliation for all 10 discrepancies; then conduct a new contract review before any implementation authorization.
```
