# Target Schema Reconciliation

**Date:** 2026-10-02
**Type:** decision and documentation reconciliation only. No source, ORM, migration, test, Docker, or runtime configuration was changed. No Alembic command, database connection, application startup, or test was run.

**Status note:** This document remains the source for the logical schema contract and the ten discrepancy classifications. Its migration-readiness statements and next gate are superseded by [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md), which records the implemented single-head design and database-free validation. PostgreSQL 16 execution remains unverified.

## 1. Executive status

The canonical logical PostgreSQL 16 schema is **DEFINED** for the inventoried 31-table ORM/runtime persistence surface. This is a schema contract, not a claim that Alembic can currently install it or that PostgreSQL-generated DDL has been runtime-verified.

All 41 application defaults are classified as application-owned. The seven persistent server defaults in historical migrations are intentionally absent from the target; each is now identified as an intentional direct-SQL behavior change. All 43 foreign keys use `NO ACTION`; the three prior cascade candidates are resolved by policy because no repository/runtime evidence requires database `CASCADE`. The system seed and dedicated migration-job operating policies are defined.

The former connected 23-revision Alembic history was **not** a clean-install graph. The ten known discrepancies below are classified as legacy migration debt or migration-produced schema gaps; none leaves the intended logical target undecided. Strategy D now archives that lineage and installs the canonical single-root baseline. Static graph and ORM-contract checks pass; PostgreSQL 16 DDL/runtime behavior remains unverified.

## 2. Three FK cascade candidates — resolved by policy

For each candidate, current migrations omit `ondelete`; the existing effective FK action is PostgreSQL `NO ACTION`. The ORM cascades are unit-of-work behavior and do not establish a database-level cascade requirement.

| Parent | Child field | Current ORM relationship | Current migration behavior | Repository/service behavior | Why CASCADE was considered | Consequence of NO ACTION | Does runtime require database CASCADE? | Decision |
|---|---|---|---|---|---|---|---|---|
| `organizations` | `organization_quotas.organization_id` | `OrganizationRecord.quotas` uses `cascade="all, delete-orphan"`. | FK has no `ondelete`; effective PostgreSQL behavior is NO ACTION. | `QuotaRepository` reads/sets quota rows and usage; no organization-delete operation was found. | Quota is organization-owned configuration and ORM marks it as an orphan-deleted child. | Deleting an organization with quota rows is rejected; explicitly remove quota rows first or retain the organization. | **No.** No repository/runtime deletion path requires automatic DB cleanup. | **RESOLVED_BY_POLICY: NO ACTION.** |
| `roles` | `role_permissions.role_id` | `RoleRecord.permissions` uses `cascade="all, delete-orphan"`. | FK has no `ondelete`; effective PostgreSQL behavior is NO ACTION. | `RBACRepository` creates roles and permission links, and reads persisted grants; no role-delete operation was found. | Link is an association row subordinate to a role; ORM treats it as a child. | Deleting a role with link rows is rejected; explicitly remove links first or retain the role. | **No.** Persisted authorization needs link rows while the role exists, but there is no role-delete runtime path requiring DB cascade. | **RESOLVED_BY_POLICY: NO ACTION.** |
| `permissions` | `role_permissions.permission_id` | `PermissionRecord.roles` uses `cascade="all, delete-orphan"`. | FK has no `ondelete`; effective PostgreSQL behavior is NO ACTION. | `RBACRepository` creates permissions and links and reads grants; no permission-delete operation was found. | Link is an association row subordinate to a permission; ORM treats it as a child. | Deleting a permission with role links is rejected; explicitly remove links first or retain the permission. | **No.** No permission-delete runtime path requires DB cascade. | **RESOLVED_BY_POLICY: NO ACTION.** |

This retains the owner’s restrictive default without mechanically mirroring ORM cascades. There are no remaining owner decisions for these three actions.

## 3. Seven legacy server-default differences

The canonical target removes each persistent database default under the selected `APPLICATION_OWNED_UNLESS_DATABASE_INVARIANT` policy. Existing ORM defaults remain. For non-ORM inserts, the caller must explicitly provide the value. No repository-supported direct-SQL writer was identified; the owner policy accepts this behavior change, and no production data exists. Local databases remain separately protected until inspected.

| Field | Historical migration behavior | Current ORM/application behavior | Target behavior | Classification | Replacement invariant and acceptance basis |
|---|---|---|---|---|---|
| `executions.status` | `0001_persistence` has server default `completed` (lowercase). | ORM default is `COMPLETED` (uppercase); execution paths can also write explicit lifecycle states. | No server default; omitted ORM value receives `COMPLETED`. | INTENTIONAL_BEHAVIOR_CHANGE | Application-created rows retain the current application value. Non-ORM writers must supply status. The owner selected application ownership; this also resolves historical case divergence. |
| `risk_policies.high_risk_threshold` | `20230912_01` has server default `0.7`. | ORM and domain fallback use `0.7`; `RiskPolicyRepository.save_policy` writes the policy value. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | Application policy creation continues to use its current value; non-ORM writers must provide the threshold. No supported raw writer is evidenced. |
| `risk_policies.critical_risk_threshold` | `20230912_01` has server default `0.9`. | ORM and domain fallback use `0.9`; `RiskPolicyRepository.save_policy` writes the policy value. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | Application policy creation continues to use its current value; non-ORM writers must provide the threshold. No supported raw writer is evidenced. |
| `channel_mappings.external_product_id` | `20260916_03` has an empty-string server default. | ORM default is an empty string. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | ORM-created records retain the current default; non-ORM writers supply the value. |
| `channel_mappings.last_synced_hash` | `20260916_03` has an empty-string server default. | ORM default is an empty string. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | ORM-created records retain the current default; non-ORM writers supply the value. |
| `channel_mappings.active` | `20260916_03` has server default `true`. | ORM default is `True`. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | ORM-created records retain the current default; non-ORM writers supply the value. |
| `compliance_policies.enabled` | `20260923_01` has server default `true`. | ORM default is `True`; repository persistence writes the domain policy value. | No server default. | INTENTIONAL_BEHAVIOR_CHANGE | Application policy writes retain the current default; non-ORM writers supply enabled explicitly. |

The prior field matrix incorrectly attributed a server default to `sync_attempts.external_product_id`. Static inspection of `20260916_02_add_sync_jobs.py` shows that the migration declares the column non-nullable but provides no `server_default`; it is not one of these seven. `20230912_04` temporarily uses an empty default to backfill approval token hashes and removes it in that same migration; it is not a persistent default difference.

`SERVER_DEFAULT_EXCEPTIONS_REMAINING = 0` means no server-default behavior difference remains unclassified; it does not mean there are no intentional behavior changes. The seven changes are all explicitly classified above.

## 4. Ten migration-history discrepancy classifications

The count is ten defined items: one PostgreSQL type incompatibility, one contradictory workspace creator, seven missing table creators, and one conditional/partial legacy-creator behavior. The seven absent creators are listed individually. “Canonical behavior” describes the target contract; it does not assert that current Alembic creates it.

| ID | Historical migration behavior | Current ORM/canonical behavior | Runtime evidence | Target-schema impact | Classification | Required future action | Implementation authorization required |
|---|---|---|---|---|---|---|---|
| H1 | `7757af5afe0a` uses raw `DATETIME` in workspace creation; known PostgreSQL 16 empty-bootstrap failure occurs there. | `WorkspaceRecord.created_at` is timezone-aware SQLAlchemy `DateTime`; PostgreSQL target mapping is `TIMESTAMP WITH TIME ZONE`. | Workspace creation/access is used by application/API services and tests; prior isolated PG16 evidence records failure at this operation. | No change to the intended target type; the migration path fails before it can establish the target. | HISTORICAL_MIGRATION_DEBT | Design a PG16-compatible workspace creation path as part of clean-install repair; preserve the ORM timestamp contract. | YES |
| H2 | Workspace is conditionally created in `7757af5afe0a`, then unconditionally created by `fcbc1a52044c`; later revision(s) alter it. | One workspace table with the ORM/runtime fields and constraints is the target. | Workspace ownership/project/API consumers use one logical workspace entity. | No second workspace object is part of the target; the history can fail or produce state-dependent results. | HISTORICAL_MIGRATION_DEBT | Reconcile the duplicate/contradictory operations in a reviewed graph repair design. | YES |
| H3 | No revision creates `projects`. | `ProjectRecord` is in the 31-table target and has a workspace FK. | Project services and workspace/project tests consume it. | Current migration output cannot include a newly provisioned project table from empty history. | CANONICAL_SCHEMA_GAP | Add the table to a future clean-install/upgrade repair design from the reconciled model inventory. | YES |
| H4 | No revision creates `datasets`; `d14c1f2a9b31` first alters it. | `DatasetRecord` is in the target with project ownership and storage/quality fields. | Dataset ingestion, storage, quality, workflow, and sync consumers use it. | Migration output is missing a required target table and a dependent revision assumes it exists. | CANONICAL_SCHEMA_GAP | Define its creation before dependent alterations in the approved graph design. | YES |
| H5 | No revision creates `workflows`. | `WorkflowRecord` is in the target with project ownership and lifecycle state. | Authoring/runtime services and workflow tests consume it. | Required target table absent from migration creator evidence. | CANONICAL_SCHEMA_GAP | Add its reconciled creation to the clean-install design. | YES |
| H6 | No revision creates `workflow_versions`. | `WorkflowVersionRecord` is in the target with workflow FK and unique version identity. | Versioning/runtime consumers and snapshot tests use it. | Required target table absent from migration creator evidence. | CANONICAL_SCHEMA_GAP | Add its reconciled creation before dependent use in the graph design. | YES |
| H7 | No revision creates `workflow_executions`; later history alters it. | `WorkflowExecutionRecord` is in the target and is the persistent workflow execution entity. | Sync/worker lifecycle, approvals, traces, and execution tests consume it. | Required target table absent; dependent revisions and runtime cannot be satisfied by current empty chain. | CANONICAL_SCHEMA_GAP | Add its reconciled creation before dependent constraints/revisions. | YES |
| H8 | No revision creates `execution_traces`. | `ExecutionTraceRecord` is in the target as legacy execution capability trace persistence. | Trace repository/persistence tests and runtime persistence consume it. | Required target persistence table absent from creator history. | CANONICAL_SCHEMA_GAP | Add its reconciled creation in the repair design. | YES |
| H9 | No revision creates `capability_execution_traces`. | `CapabilityExecutionTraceRecord` is in the target for workflow capability execution traces. | Workflow trace persistence and worker/runtime tests consume it. | Required target persistence table absent from creator history. | CANONICAL_SCHEMA_GAP | Add its reconciled creation before trace writes. | YES |
| H10 | `0001_persistence` branches on table existence and only partially reconciles users/executions/reports/logs; `c13a7e91d204` conditionally creates `agent_memory` if absent and does not reconcile arbitrary partial table shapes. | Complete target tables and constraints are those in current ORM metadata. | User/execution persistence, validation/report consumers, memory persistence and tests use these records. | Result depends on predecessor schema and may leave missing objects or mismatched columns; target definitions themselves remain supplied by ORM/runtime evidence. | HISTORICAL_MIGRATION_DEBT | Define supported predecessor states and deterministic repair behavior; do not treat these conditionals as a general baseline reconciler. | YES |

All ten items are classified. The seven absent tables are schema gaps in what the current migration path can create, not unresolved decisions about whether those application tables belong in the target. No discrepancy is classified as an unresolved target-schema decision or an obsolete artifact.

## 5. Target schema versus migration path

For this table, `AFFECTS_TARGET_SCHEMA` means the current history, if used as written, can fail to produce the contract (including an incomplete result); `CANONICAL_SCHEMA_DECISION_REQUIRED` asks separately whether the desired schema semantics are unknown.

| Discrepancy | Affects target schema | Affects migration path | Canonical schema decision required |
|---|---|---|---|
| H1 — PostgreSQL-incompatible `DATETIME` | NO — intended workspace field type is already determined by ORM mapping. | YES — migration fails on PostgreSQL 16. | NO |
| H2 — duplicate/contradictory workspace creation | YES — current history can fail or create state-dependent workspace schema. | YES | NO — single target entity and shape are defined by ORM/runtime inventory. |
| H3 — missing `projects` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H4 — missing `datasets` creator | YES — resulting schema lacks a required target table and dependent alteration fails. | YES | NO |
| H5 — missing `workflows` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H6 — missing `workflow_versions` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H7 — missing `workflow_executions` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H8 — missing `execution_traces` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H9 — missing `capability_execution_traces` creator | YES — resulting schema lacks a required target table. | YES | NO |
| H10 — conditional/partial legacy creators | YES — resulting object set/shape depends on predecessor state. | YES | NO — the complete target is specified by the ORM inventory; predecessor repair is graph work. |

The `YES` target-impact values describe the broken schema that the present history can produce, not ambiguity in the canonical 31-table target. H1 is path-only because it fails before producing the intended schema type.

## 6. Canonical target-schema readiness

All gate elements are met at the **logical contract** level:

- 31 ORM tables are inventoried and are the defined logical persistence surface.
- All 41 application defaults have the application-owned policy. The seven persistent server-default differences are individually classified above as intentional behavior changes; none remains unclassified.
- All 43 FKs use `NO ACTION`; the three cascade candidates are resolved by policy, not left as owner decisions.
- System seed is limited to the persisted RBAC role, permission, and link catalogue; it is separate from schema migrations, initial admin provisioning, and demo data.
- PostgreSQL 16, first-production/no-historical-baseline scope, dedicated migration-job order, and no automatic app-startup migration are explicit.
- All ten history discrepancies are classified. None requires a new choice about canonical table membership/default/FK semantics.

Therefore `CANONICAL_TARGET_SCHEMA = DEFINED` means the logical contract is settled. It does **not** mean DDL has been emitted/verified against PostgreSQL 16, Alembic is repaired, deployment is ready, or implementation is authorized.

## 7. Migration repair readiness

`MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB` is selected. The former connected 23-revision history was not a valid clean-install graph for the ten reasons above. The approved single-head repair is implemented as `20261002_01`, with the old revisions preserved in the inactive archive. This is static implementation evidence only; no Alembic command or database operation was run. See [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md).

## 8. Remaining owner decisions

`SCHEMA_DECISIONS_REMAINING = 0` for canonical schema semantics. There are no remaining FK cascade, default, seed, or operating-model owner decisions in this pass. Deployment details, local DB classification, migration-job security, backup/restore procedures, and PostgreSQL runtime verification are implementation/operational preconditions, not open choices about the canonical schema. `LOCAL_STATE = PRESERVE_UNTIL_INSPECTED` remains binding for local files/volumes.

## 9. Exact implementation preconditions

Before any implementation authorization:

1. Review/approve a detailed single-head Alembic repair design for the ten classified discrepancies; do not begin from this contract alone.
2. Correct and verify the repair plan against all 31 table definitions, 41 defaults, 43 FKs, indexes, uniqueness, identity behavior, and RBAC seed contract.
3. Preserve and separately classify tracked SQLite data and persistent Compose volumes; do not treat them as production baselines or disposable state.
4. Define isolated PostgreSQL 16 validation, schema fingerprint checks, startup checks (`create_schema=False`), representative operations, and rollback/recovery evidence. No SQLite substitution.
5. Include tests/release notes for seven direct-SQL default behavior changes, even though ORM default behavior is preserved.
6. Define dedicated migration-job serialization, least-privilege DDL identity, secret delivery, schema-validation failure behavior, and backup/restore expectations.
7. Obtain explicit implementation authorization for a specific repair slice. This document grants none.

## 10. Historical next gate — superseded

The earlier recommendation to approve and implement the repair is complete. The current next gate is explicit authorization for isolated PostgreSQL 16 validation. The implementation authorization did not include database access; no migration command has run.

```text
CANONICAL_TARGET_SCHEMA = DEFINED
SCHEMA_DECISIONS_REMAINING = 0
SERVER_DEFAULT_EXCEPTIONS_REMAINING = 0
MIGRATION_HISTORY_DISCREPANCIES = 10
UNRESOLVED_TARGET_SCHEMA_DECISIONS = 0
MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB
MIGRATION_GRAPH_STATUS = IMPLEMENTED_STATICALLY
IMPLEMENTATION_AUTHORIZATION = GRANTED_AND_USED_FOR_ALEMBIC_REPAIR_ONLY
POSTGRESQL_16_VALIDATION = NOT_AUTHORIZED
NEXT_GATE = Obtain explicit authorization for isolated PostgreSQL 16 validation.
```
