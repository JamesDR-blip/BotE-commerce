# First Production Provisioning Assessment

**Historical status:** This evidence snapshot predates the owner-approved canonical contract and Strategy D implementation. Its old gate result is superseded by [`CANONICAL_SCHEMA_CONTRACT.md`](CANONICAL_SCHEMA_CONTRACT.md), [`TARGET_SCHEMA_RECONCILIATION.md`](TARGET_SCHEMA_RECONCILIATION.md), and [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md). The ORM inventory remains useful as implementation evidence; PostgreSQL runtime behavior remains unverified.

**Date:** 2026-10-02  
**Mode:** assessment and repair design only  
**Implementation status:** no code, tests, models, migrations, runtime configuration, databases, or containers changed or operated for this assessment.

## Decision summary

The project owner has explicitly confirmed that the project has run only locally/development, has never been deployed to production or staging, has no production PostgreSQL database, no production data, and no authoritative historical production schema. PostgreSQL 16 is the intended future production engine. This owner-provided fact supersedes the earlier assumption that an external production baseline might exist and reframes the work as **FIRST_PRODUCTION_PROVISIONING**, not production-schema takeover.

```text
PRODUCTION_DATABASE_EXISTS = NO
PRODUCTION_DATA_EXISTS = NO
STAGING_DATABASE_EXISTS = NO
AUTHORITATIVE_HISTORICAL_PRODUCTION_SCHEMA = NO
PHASE_5_MODE = FIRST_PRODUCTION_PROVISIONING
```

This removes the production-data preservation blocker. It does not make the current migrations executable, establish a canonical schema specification, prove local/development database states, or authorize repair. The current Alembic chain is not a valid empty PostgreSQL 16 bootstrap. `database.models.Base.metadata` is a useful candidate schema inventory, but it is not by itself a complete approved target specification.

**Assessment result:** `FIRST_PRODUCTION_PROVISIONING = REPAIR_DESIGN_BLOCKED`  
**Canonical target:** `NOT_YET_DEFINED`  
**Migration strategy:** `UNDECIDED`  
**Repair authorization:** `NOT_AUTHORIZED`  
**Implementation authorization:** `NOT_AUTHORIZED`

## Evidence and scope

- The owner supplied the no-production/no-staging/no-production-data facts above. This is the authority for environment history; repository forensics cannot prove absence of untracked deployment activity.
- `database/migrations/versions` contains 23 revisions and one current head, `20260928_01` (static repository history already recorded in Phase 5A; no Alembic command was run for this assessment).
- The Phase 5A report records the PostgreSQL 16 failure at `7757af5afe0a` on raw `DATETIME`, no migration creator for `datasets` and multiple other ORM tables, and the later conflicting workspace creator `fcbc1a52044c`.
- `database.models.Base.metadata` currently declares **31 tables**. It was inspected by importing model declarations only; no engine/session factory, `create_all()`, database connection, or migration was invoked.
- `database.models.make_session_factory()` defaults `create_schema=True`, while the current container passes `create_schema=False` in production and requires the repository head there. In development/test it requests `create_all()`. That runtime convenience is not selected as the production provisioning mechanism.
- Tests predominantly call `Base.metadata.create_all()` against SQLite or test-local engines. They establish application/repository behavior for those fixtures, not PostgreSQL migration equivalence. No PostgreSQL integration test service is declared in CI.
- A prior empty disposable PostgreSQL 16.15 database was documented as `aeop-postgres16-verify` / `dataquality_verify`. It is not production/staging and contributes no historical baseline.

### Historical evidence versus target specification

The current ORM model inventory below is the best code-derived candidate for the current persistence surface. It does not settle PostgreSQL-specific type rendering, server-side versus Python defaults, required seed/reference rows, legacy/runtime tables, deletion/retention behavior, constraint naming, or the desired treatment of all formerly conditional migration branches. Tests that construct SQLite schemas do not close those questions. A reviewed target must combine ORM metadata with repository write/read contracts, domain invariants, test fixtures, and PostgreSQL-specific requirements.

## Current ORM table inventory

Notation: `*` means primary key; `->table.column` means foreign key; `?` means nullable; `[py]` means a SQLAlchemy/Python-side default, not a server default. Unmarked columns are non-nullable in the inspected metadata. `DT` is SQLAlchemy `DateTime`; the timezone flag is column-specific. There are 26 `DateTime(timezone=True)` columns and six `DateTime(timezone=False)` trace timestamps (`execution_traces` and `capability_execution_traces`: `started_at`, `finished_at`, `created_at`). PostgreSQL rendering remains unverified. `JSON`, `TEXT`, `BOOL`, `INT`, `FLOAT`, and `VARCHAR(n)` are the declared generic SQLAlchemy types. Declared status/category/risk values are strings, not PostgreSQL enum types. Indexes listed are ORM-declared index names; unique constraints are called out separately.

| Table | Declared columns | Unique constraints | Indexes | Alembic provenance |
|---|---|---|---|---|
| `agent_memory` | `id* VARCHAR(36)`; `workspace_id ->workspaces.id VARCHAR(36)`; `user_id ->users.id VARCHAR(36)`; `memory_type VARCHAR(64)`; `memory_key VARCHAR(255)`; `value_json TEXT`; `created_at DT`; `expires_at DT?` | none declared | `ix_agent_memory_expires_at`, `ix_agent_memory_scope_type_key`, `ix_agent_memory_user_id`, `ix_agent_memory_workspace_id` | `c13a7e91d204` conditionally creates; requires users/workspaces |
| `approvals` | `approval_id* VARCHAR(36)`; `execution_id ->workflow_executions.id VARCHAR(36)`; `changeset_id ->changesets.id VARCHAR(36)`; `risk_score VARCHAR(20)`; `confidence_score FLOAT`; `requested_by VARCHAR(255)`; `created_at DT [py]`; `expires_at DT?`; `decision VARCHAR(20)?`; `token_hash VARCHAR(64)` | none declared | `ix_approvals_changeset_id`, `ix_approvals_execution_id` | `20230912_01` creates initial table; `20230912_02`, `20230912_04`, `20260914_02` alter it; final table depends on workflow/ChangeSet objects |
| `audit_events` | `id* VARCHAR(36)`; `workspace_id ->workspaces.id VARCHAR(36)`; `actor_id ->users.id VARCHAR(36)`; `action VARCHAR(100)`; `resource_type VARCHAR(100)`; `resource_id VARCHAR(36)`; `execution_id ->workflow_executions.id VARCHAR(36)?`; `changeset_id ->changesets.id VARCHAR(36)?`; `metadata_json JSON [py]`; `created_at DT [py]`; `previous_hash VARCHAR(64)?`; `event_hash VARCHAR(64)` | none declared | `ix_audit_events_actor_id`, `ix_audit_events_changeset_id`, `ix_audit_events_created_at`, `ix_audit_events_event_hash`, `ix_audit_events_execution_id`, `ix_audit_events_resource_id`, `ix_audit_events_workspace_id` | `20260914_03` creates; prerequisite tables are not all created by the chain |
| `capability_execution_traces` | `id* VARCHAR(36) [py]`; `workflow_execution_id ->workflow_executions.id VARCHAR(36)`; `capability_id VARCHAR(100)`; `capability_version VARCHAR(50)`; `status VARCHAR(50)`; `inputs_json TEXT?`; `outputs_json TEXT?`; `started_at DT?`; `finished_at DT?`; `duration_ms FLOAT?`; `error TEXT?`; `created_at DT [py]` | none declared | `ix_capability_execution_traces_workflow_execution_id` | no creator found |
| `changeset_items` | `id* VARCHAR(36)`; `changeset_id ->changesets.id VARCHAR(36)`; `entity VARCHAR(100)`; `record_id VARCHAR(255)`; `before_snapshot JSON`; `after_snapshot JSON` | none declared | `ix_changeset_items_changeset_id` | `20260914_01` creates; referenced by `20260928_01` |
| `changesets` | `id* VARCHAR(36)`; `dataset_id ->datasets.id VARCHAR(36)`; `execution_id ->workflow_executions.id VARCHAR(36)`; `workflow_id ->workflows.id VARCHAR(36)`; `workflow_version VARCHAR(50)`; `before_storage_key TEXT`; `before_content_hash VARCHAR(64)`; `after_storage_key TEXT`; `after_content_hash VARCHAR(64)`; `integrity_hash VARCHAR(64)`; `status VARCHAR(20)`; `created_at DT [py]`; `applied_at DT?`; `rolled_back_at DT?` | none declared | `ix_changesets_created_at`, `ix_changesets_dataset_id`, `ix_changesets_execution_id`, `ix_changesets_status`, `ix_changesets_workflow_id` | `20260914_01` creates; `20260926_01` adds/backfills integrity hash; `20260928_01` recomputes it from item snapshots |
| `channel_mappings` | `id* VARCHAR(36)`; `channel_id ->channels.id VARCHAR(36)`; `canonical_product_id VARCHAR(255)`; `channel_type VARCHAR(50)`; `external_product_id VARCHAR(255) [py]`; `last_synced_hash VARCHAR(64) [py]`; `active BOOL [py]`; `created_at DT [py]` | `(channel_id, canonical_product_id)` | `ix_channel_mappings_canonical_product_id`, `ix_channel_mappings_channel_id`, `ix_channel_mappings_created_at` | `20260916_03` creates |
| `channels` | `id* VARCHAR(36)`; `workspace_id ->workspaces.id VARCHAR(36)`; `channel_type VARCHAR(50)`; `name VARCHAR(255)`; `credentials_encrypted TEXT`; `enabled BOOL [py]`; `created_at DT [py]` | `(workspace_id, channel_type, name)` | `ix_channels_created_at`, `ix_channels_workspace_id` | `20260916_01` creates; requires workspaces |
| `compliance_policies` | `id* VARCHAR(36)`; `organization_id ->organizations.id VARCHAR(36)`; `name VARCHAR(255)`; `resource VARCHAR(100)`; `action VARCHAR(100)`; `condition JSON [py]`; `reason TEXT`; `enabled BOOL [py]` | `(organization_id, name)` | `ix_compliance_policies_organization_id` | `20260923_01` creates |
| `data_lineage_events` | `id* VARCHAR(36)`; `dataset_id ->datasets.id VARCHAR(36)`; `execution_id ->workflow_executions.id VARCHAR(36)`; `workflow_id ->workflows.id VARCHAR(36)`; `workflow_version VARCHAR(50)`; `capability_id VARCHAR(100)`; `capability_version VARCHAR(50)`; `event_type VARCHAR(50)`; `input_refs_json JSON [py]`; `output_refs_json JSON [py]`; `created_at DT [py]` | none declared | `ix_data_lineage_events_created_at`, `ix_data_lineage_events_dataset_id`, `ix_data_lineage_events_execution_id`, `ix_data_lineage_events_workflow_id` | `20260914_03` creates; several dependencies lack creators |
| `datasets` | `id* VARCHAR(36)`; `project_id ->projects.id VARCHAR(36)`; `name VARCHAR(255)`; `source_type VARCHAR(50)`; `filename VARCHAR(255)?`; `file_format VARCHAR(20)?`; `size_bytes INT?`; `content_hash VARCHAR(64)?`; `storage_key TEXT?`; `row_count INT?`; `column_count INT?`; `status VARCHAR(30) [py]`; `metadata_json JSON [py]`; `created_at DT [py]` | none declared | `ix_datasets_content_hash`, `ix_datasets_project_id`, `ix_datasets_status` | no creator found; `d14c1f2a9b31` alters it and is the first migration reference |
| `execution_traces` | `id* VARCHAR(36) [py]`; `execution_id ->executions.id VARCHAR(36)`; `capability_id VARCHAR(100)`; `capability_version VARCHAR(50)`; `status VARCHAR(50)`; `inputs_json TEXT?`; `outputs_json TEXT?`; `started_at DT?`; `finished_at DT?`; `duration_ms FLOAT?`; `error TEXT?`; `created_at DT [py]` | none declared | `ix_execution_traces_execution_id` | no creator found |
| `executions` | `id* VARCHAR(36)`; `user_id ->users.id VARCHAR(36)?`; `dataset_id ->datasets.id VARCHAR(36)?`; `category VARCHAR(100)`; `source_hash VARCHAR(64)`; `rule_version VARCHAR(64)`; `health_score FLOAT`; `status VARCHAR(20) [py]`; `created_at DT [py]`; `requirement_json TEXT?`; `plan_json TEXT?`; `planner_version VARCHAR(50)?` | none declared | `ix_executions_category`, `ix_executions_created_at`, `ix_executions_dataset_id`, `ix_executions_source_hash`, `ix_executions_user_id` | `0001_persistence` conditionally creates/alter; `f3a4b5c6d7e8` adds dataset FK/column |
| `memberships` | `id* VARCHAR(36)`; `user_id ->users.id VARCHAR(36)`; `organization_id ->organizations.id VARCHAR(36)`; `role_id ->roles.id VARCHAR(36)`; `created_at DT [py]` | `(user_id, organization_id, role_id)` | `ix_memberships_created_at`, `ix_memberships_organization_id`, `ix_memberships_role_id`, `ix_memberships_user_id` | `20260916_04` creates |
| `organization_quotas` | `id* VARCHAR(36)`; `organization_id ->organizations.id VARCHAR(36)`; `dimension VARCHAR(50)`; `limit INT` | `(organization_id, dimension)` | `ix_organization_quotas_organization_id` | `20260922_01` creates |
| `organizations` | `id* VARCHAR(36)`; `name VARCHAR(255)`; `created_at DT [py]` | none declared | `ix_organizations_created_at` | `20260916_04` creates |
| `permissions` | `id* VARCHAR(36)`; `resource VARCHAR(100)`; `action VARCHAR(100)` | `(resource, action)` | none declared | `20260916_04` creates |
| `projects` | `id* VARCHAR(36)`; `workspace_id ->workspaces.id VARCHAR(36)`; `name VARCHAR(255)`; `description TEXT?`; `created_at DT [py]` | none declared | `ix_projects_workspace_id` | no creator found |
| `reports` | `id* INT`; `execution_id ->executions.id VARCHAR(36)`; `format VARCHAR(12)`; `path TEXT`; `metadata_json JSON [py]` | none declared | `ix_reports_execution_id` | `0001_persistence` creates only on one conditional branch |
| `risk_assessments` | `id* VARCHAR(36)`; `execution_id ->workflow_executions.id VARCHAR(36)`; `risk_score VARCHAR(20)`; `confidence_score FLOAT`; `approval_required BOOL`; `created_at DT [py]` | none declared | `ix_risk_assessments_execution_id` | `20230912_03` creates; requires workflow executions |
| `risk_policies` | `id* INT`; `high_risk_threshold FLOAT [py]`; `critical_risk_threshold FLOAT [py]` | none declared | none declared | `20230912_01` creates |
| `role_permissions` | `role_id* ->roles.id VARCHAR(36)`; `permission_id* ->permissions.id VARCHAR(36)` | composite PK `(role_id, permission_id)` and declared unique constraint on same pair | none declared | `20260916_04` creates |
| `roles` | `id* VARCHAR(36)`; `name VARCHAR(50)`; `description VARCHAR(255)?` | `(name)` | none declared | `20260916_04` creates |
| `sync_attempts` | `id* VARCHAR(36)`; `sync_job_id ->sync_jobs.id VARCHAR(36)`; `attempt_number INT`; `status VARCHAR(30)`; `request_hash VARCHAR(64)`; `external_product_id VARCHAR(255) [py]`; `error TEXT?`; `created_at DT [py]` | `(sync_job_id, attempt_number)` | `ix_sync_attempts_created_at`, `ix_sync_attempts_status`, `ix_sync_attempts_sync_job_id` | `20260916_02` creates |
| `sync_jobs` | `id* VARCHAR(36)`; `workspace_id ->workspaces.id VARCHAR(36)`; `dataset_id ->datasets.id VARCHAR(36)`; `channel_id ->channels.id VARCHAR(36)`; `idempotency_key VARCHAR(255)`; `status VARCHAR(30)`; `error TEXT?`; `created_at DT [py]` | `(workspace_id, idempotency_key)` | `ix_sync_jobs_channel_id`, `ix_sync_jobs_created_at`, `ix_sync_jobs_dataset_id`, `ix_sync_jobs_status`, `ix_sync_jobs_workspace_id` | `20260916_02` creates; depends on absent dataset/workspace creators |
| `users` | `id* VARCHAR(36)`; `email VARCHAR(255)`; `display_name VARCHAR(255)?`; `created_at DT [py]` | none in current ORM metadata | `ix_users_created_at`, `ix_users_email` | `0001_persistence` conditionally creates unique email in migration; ORM metadata does not declare that unique constraint |
| `validation_logs` | `id* INT`; `execution_id ->executions.id VARCHAR(36)`; `row_number INT`; `field VARCHAR(100)`; `code VARCHAR(100)`; `message TEXT`; `severity VARCHAR(20)` | none declared | `ix_validation_logs_execution_id` | `0001_persistence` creates only when executions is absent |
| `workflow_executions` | `id* VARCHAR(36)`; `workflow_id ->workflows.id VARCHAR(36)`; `dataset_id ->datasets.id VARCHAR(36)?`; `workflow_version VARCHAR(50)`; `status VARCHAR(20)`; `inputs_json TEXT?`; `outputs_json TEXT?`; `error TEXT?`; `started_at DT?`; `finished_at DT?`; `created_at DT [py]` | none declared | `ix_workflow_executions_created_at`, `ix_workflow_executions_dataset_id`, `ix_workflow_executions_workflow_id` | no creator found; `e2f3a4b5c6d7` alters it |
| `workflow_versions` | `id* VARCHAR(36)`; `workflow_id ->workflows.id VARCHAR(36)`; `version VARCHAR(50)`; `plan_json TEXT`; `created_at DT [py]` | `(workflow_id, version)` | `ix_workflow_versions_workflow_id` | no creator found |
| `workflows` | `id* VARCHAR(36)`; `project_id ->projects.id VARCHAR(36)`; `name VARCHAR(255)`; `active_version VARCHAR(50) [py]`; `status VARCHAR(20) [py]`; `created_at DT [py]` | none declared | `ix_workflows_project_id` | no creator found |
| `workspaces` | `id* VARCHAR(36)`; `owner_id ->users.id VARCHAR(36)`; `organization_id ->organizations.id VARCHAR(36)?`; `name VARCHAR(255)`; `created_at DT [py]` | none declared | `ix_workspaces_created_at`, `ix_workspaces_organization_id`, `ix_workspaces_owner_id` | `7757af5afe0a` has invalid raw DDL; `fcbc1a52044c` unconditionally creates the same table; `b05fd7d45c87` tightens owner nullability |

### Relationship declarations

Current ORM relationships are: organizations→memberships/workspaces/quotas; roles↔memberships/role_permissions; permissions↔role_permissions; users→executions/workspaces/memberships; workspaces→owner/organization/projects; projects→workspace/datasets/workflows; datasets→project; workflows→project/versions/executions; workflow versions→workflow; workflow executions→workflow/capability traces/approvals/risk assessments; executions→user/reports/logs/execution traces; reports/logs/traces→execution; capability traces→workflow execution; changesets↔items; items→changeset; approvals/risk assessments→workflow execution; memberships→user/organization/role; quotas→organization; all other ORM mappings declare no relationship property. Foreign-key declarations still apply even where an ORM relationship is not declared.

### Schema-target gaps requiring an explicit decision

- The ORM and Alembic differ on at least `users.email`: `0001_persistence` creates it unique, while the current ORM metadata does not declare that uniqueness. This is not a harmless assumption; repositories and authentication behavior must establish the intended invariant.
- ORM Python defaults are not server defaults. A direct SQL writer or another service may not receive the same values. Review actual consumers before freezing server-default semantics.
- The final table set contains 31 ORM tables; 23 historical revisions do not create every table. In particular, no creator exists for `projects`, `datasets`, `workflows`, `workflow_versions`, `workflow_executions`, `execution_traces`, or `capability_execution_traces`.
- `approvals`, `changesets`, lineage, audit, and traces depend on the workflow and dataset graph. FK nullability and ordering must preserve existing API, worker, and integrity behavior.
- Audit event hash chaining, ChangeSet metadata/item hashes, sync idempotency constraints, ownership constraints, and approval token hashing are behavior contracts beyond merely creating columns.
- The repository evidence found no migration-declared PostgreSQL extensions or native enum types. Do not add them without a concrete contract.
- The exact seed/reference policy for roles/permissions, risk policy rows, compliance policies, quotas, and demo workspaces is not established as part of a first-install migration. Repository searches found repository APIs and tests that explicitly create policy records, but did not establish an authoritative default seed set.
- `data_quality.db` and SQLite test fixtures are not schema authorities.

## Migration-history classification

Class labels are the requested primary forensic classification for the **existing in-place chain**. “Keep as historical” means preserve the file/evidence, not necessarily use the revision in the eventual first-production path. The target strategy is not yet selected.

| Revision | Class | Evidence and consequence for fresh PostgreSQL 16 |
|---|---|---|
| `0001_persistence` | F — DEPENDS ON PRE-EXISTING SCHEMA | Conditional table-name branches do not reconcile every partial state; revision text describes an existing execution persistence schema. |
| `7757af5afe0a` | E — CONFLICTING | Raw `DATETIME` fails on PostgreSQL 16; current file conditionally creates workspaces while historical intent assumed one existed; a later revision creates it unconditionally. |
| `b05fd7d45c87` | F — DEPENDS ON PRE-EXISTING SCHEMA | Requires workspace ownership state and deletes the `ws-demo` row when owner is NULL; downgrade cannot restore the row. Fresh baseline should decide whether this historical cleanup is excluded. |
| `c13a7e91d204` | F — DEPENDS ON PRE-EXISTING SCHEMA | Agent-memory DDL requires users and workspaces. |
| `d14c1f2a9b31` | F — DEPENDS ON PRE-EXISTING SCHEMA | Alters `datasets`, but no prior migration creates it. |
| `e2f3a4b5c6d7` | F — DEPENDS ON PRE-EXISTING SCHEMA | Alters workflow executions and adds dataset FK; neither required base table is created by this chain. |
| `f3a4b5c6d7e8` | F — DEPENDS ON PRE-EXISTING SCHEMA | Alters executions and adds dataset FK; requires datasets and expected execution state. |
| `20230912_01` | A — KEEP AS HISTORICAL | Creates risk policies and approvals as a feature increment; unguarded creates can conflict with a pre-provisioned metadata schema. |
| `20230912_02` | F — DEPENDS ON PRE-EXISTING SCHEMA | Approval FK alteration requires approvals and workflow executions, the latter lacking a creator. |
| `fcbc1a52044c` | E — CONFLICTING | Unconditionally creates workspaces after `7757af5afe0a`; downgrade is a no-op. |
| `20230912_03` | F — DEPENDS ON PRE-EXISTING SCHEMA | Risk assessments reference workflow executions, with no chain creator. |
| `20230912_04` | F — DEPENDS ON PRE-EXISTING SCHEMA | Alters approvals; assumes the expected table and column state. |
| `20260914_01` | F — DEPENDS ON PRE-EXISTING SCHEMA | Creates ChangeSets, but requires datasets, executions, workflow executions, and workflows. |
| `20260914_02` | F — DEPENDS ON PRE-EXISTING SCHEMA | Alters approvals and depends on ChangeSets and expected approval state. |
| `20260914_03` | F — DEPENDS ON PRE-EXISTING SCHEMA | Creates lineage/audit but references datasets, workflow executions, workflows, workspaces, users, and ChangeSets. |
| `20260916_01` | F — DEPENDS ON PRE-EXISTING SCHEMA | Creates channels and requires workspace lifecycle consistency. |
| `20260916_02` | F — DEPENDS ON PRE-EXISTING SCHEMA | Creates sync jobs/attempts but requires datasets, channels, and workspaces. |
| `20260916_03` | A — KEEP AS HISTORICAL | Creates channel mappings after channels; preserve its behavior and contract as historical evidence. |
| `20260916_04` | F — DEPENDS ON PRE-EXISTING SCHEMA | Creates org/RBAC tables and alters workspaces; requires compatible users/workspace state. |
| `20260922_01` | A — KEEP AS HISTORICAL | Creates quotas after organizations exist. |
| `20260923_01` | A — KEEP AS HISTORICAL | Creates compliance policies after organizations exist. |
| `20260926_01` | F — DEPENDS ON PRE-EXISTING SCHEMA | Backfills ChangeSet integrity hashes and makes them non-null; assumes populated tables/columns. |
| `20260928_01` | F — DEPENDS ON PRE-EXISTING SCHEMA | Recomputes hashes from ChangeSet items; requires those tables and compatible JSON snapshots. |

No revision is classified as **B — SAFE TO REPAIR** in isolation: a type-only edit does not make the chain complete, and the runtime target and local database states are not fully specified. No revision is inherently **D — REDUNDANT** in the existing history. A new baseline could supersede their use for future first installs while retaining the old files; that is a strategy proposal, not a current classification.

## Intended first-production target behavior

The target should be a PostgreSQL 16 schema that supports the current application persistence contracts, with one reviewed and repeatable Alembic provisioning path. It must retain current table-level behavior for identity/ownership/RBAC, datasets/projects/workflows, sync jobs and idempotency, execution and traces, audit/lineage, approvals/risk/compliance/quota, ChangeSet integrity, and agent memory. It should use the current ORM inventory as a reconciliation input, not blindly translate every ORM declaration into DDL.

Before the target can be called defined, approve: exact schema/table/column/type/null/default semantics; all PK/FK/unique/index constraints; identity/sequence behavior; timezone behavior; JSON storage; seed/reference rows; audit and ChangeSet integrity invariants; compatible transaction and repository operations; required grants/extensions; and one Alembic revision identity for an empty PostgreSQL 16 database. The first future production provisioning should not include data migration from a nonexistent production system, but should still preserve local/development users' explicitly supported database states or clearly document their disposition.

## First-production deployment sequence (design only)

1. Provision PostgreSQL 16 and a dedicated database/owner through the approved infrastructure process.
2. Inject unique production credentials through the approved secret store; do not use developer or local-stage secrets.
3. Ensure database/schema ownership, required grants, encoding, and required extensions match the approved target specification.
4. Run the single selected Alembic provisioning path once as a release/deployment job before API or worker startup. Do not run migrations in every API/worker replica.
5. Verify `alembic current` equals the reviewed target head and compare schema inventory/fingerprint with the approved target.
6. Start API instances only after migration verification; production startup must verify revision and must not create schema.
7. Start workers only after the same schema gate; workers must not create schema or independently migrate.
8. Start dashboard after API health is established; dashboard is an HTTP client, not a schema provisioner.
9. Run smoke operations for auth/RBAC, dataset persistence, representative workflow sync and async execution, trace/report persistence, audit/lineage, ChangeSet integrity and approval behavior.
10. Establish automated backup before accepting production data; verify backup artifacts and retention.
11. Restore into an isolated PostgreSQL 16 database, verify schema/revision and representative records, then repeat the smoke operations.

This is a future sequence, not deployment authorization. A migration job location and deployment ordering must be selected before implementation. API startup, worker startup, and dashboard startup are **not** migration runners.

## Tests required before first-production authorization

No tests were executed for this assessment. Before selecting/implementing a strategy, plan:

1. Fresh empty PostgreSQL 16 bootstrap from the selected Alembic path.
2. Verify one current Alembic head, `alembic current`, and the expected version-table row.
3. Compare all 31 required ORM/application tables against an approved table/column/constraint/index/sequence/default inventory; investigate intended differences rather than requiring blind metadata equality.
4. API startup against the migrated PostgreSQL database without schema creation.
5. Worker startup against the same migrated database without schema creation.
6. Representative CRUD/persistence through repositories for datasets, users/workspaces/projects, workflows, execution/traces, memory, channels/sync, RBAC/compliance/risk, audit/lineage, and ChangeSets/approvals.
7. Workflow execution tests that verify sync/worker state and trace/report persistence against PostgreSQL; do not infer PostgreSQL behavior from current SQLite tests.
8. Audit hash-chain and ChangeSet metadata/item integrity round-trip tests.
9. Backup and restore rehearsal on a separate isolated database with integrity checks.
10. Two consecutive fresh provisionings from the same pinned migration/image version producing the same schema fingerprint.

## Unresolved decisions

- Is the first-install active history an in-place repaired linear chain, a separately versioned clean-install lineage that preserves old files, or another reviewed approach?
- Which local/development database states and Alembic revisions exist and must remain upgradeable? The owner established no production/staging, not that no local database has applied revisions.
- Are current ORM table/column/default declarations the intended database contract, or are deliberate differences required (including `users.email` uniqueness and server defaults)?
- What seed/reference records are required for usable first install, and which are explicitly operator-provisioned?
- Should the current `create_all()` use in development/test remain as-is, be restricted to isolated tests, or be separated from development startup after separate authorization?
- What grants, schema owner, backup/retention policy, and exact deployment migration job are required?
- Which PostgreSQL 16 minor and immutable image digest should be pinned in CI/deployment verification?

## Gate

The change in premise closes the historical production-evidence question: there is no production baseline to acquire or take over. Phase 5 now concerns first-provisioning correctness. It remains blocked at repair design because the full target is not formally specified, the current chain cannot bootstrap empty PostgreSQL 16, and local-development Alembic state compatibility has not been inventoried.

```text
PRODUCTION_DATABASE_EXISTS = NO
PRODUCTION_DATA_EXISTS = NO
STAGING_DATABASE_EXISTS = NO
AUTHORITATIVE_HISTORICAL_PRODUCTION_SCHEMA = NO
PHASE_5_MODE = FIRST_PRODUCTION_PROVISIONING
CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
MIGRATION_STRATEGY = UNDECIDED
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```
