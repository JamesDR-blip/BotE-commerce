# Schema Decision Register

**Date:** 2026-10-02

**Scope:** repository-evidence decisions only. No database connection, SQL, Alembic command, test, application startup, migration, or schema change was performed.

**Companion inventory:** [SUPPORTED_LOCAL_DATABASE_STATES.md](SUPPORTED_LOCAL_DATABASE_STATES.md).

**Schema inventory:** [CANONICAL_SCHEMA_RECONCILIATION.md](CANONICAL_SCHEMA_RECONCILIATION.md).

**Current decision status:** the `FINAL TARGET-SCHEMA / MIGRATION-HISTORY RECONCILIATION` section at the end of this register is authoritative. The original discovery decisions, gate, and first owner-policy overlay below are preserved as historical snapshots and are explicitly superseded by that section and its linked matrices.

## Status key

- **RESOLVED_BY_EVIDENCE** — current repository behavior or a concrete source fact is established. This does not imply PostgreSQL runtime validation.
- **EXPLICIT_PRODUCT_DECISION_REQUIRED** — code offers behavior but the durable/operational contract is not selected by repository evidence.
- **BLOCKED_BY_MISSING_EVIDENCE** — needed environment, predecessor state, or production-compatible validation evidence is absent.

## Decisions — historical discovery snapshot, superseded 2026-10-02

| Decision | Current evidence | Status | Proposed contract, only where supported | Remaining uncertainty |
|---|---|---|---|---|
| 1. `users.email` uniqueness and lookup | Current ORM `UserRecord.email` is `unique=True, index=True` (`database/models.py`); SQLAlchemy metadata inspection shows one unique index `ix_users_email`, not a separately declared unique constraint plus separate index. `0001_persistence` creates email with `unique=True` and explicitly creates `ix_users_email`. `UserRepository.get_by_email` uses exact equality. No lower/casefold/normalization in this repository lookup. | RESOLVED_BY_EVIDENCE | One logical unique, exact-value email key with an index usable by equality lookup. Current ORM expresses the index as unique; `0001` expresses a unique constraint plus a separately named non-unique index, which may be physically redundant. No case-insensitive uniqueness/canonicalization is part of the evidenced repository contract. | PostgreSQL physical objects and collation were not inspected; identity/authentication layer outside this repository may normalize before calling the repository. Do not add case-fold behavior absent evidence. |
| 2. ORM Python defaults vs server defaults | Metadata inspection found no ORM `server_default`; Python/SQLAlchemy-side defaults are listed below. Historical migrations explicitly contain server defaults for execution status, risk thresholds, approval token temporary backfill, channel-mapping values, and compliance enabled. SQLAlchemy defaults apply to ORM-generated INSERTs, not arbitrary SQL clients. | EXPLICIT_PRODUCT_DECISION_REQUIRED | Preserve the currently evidenced distinction: ORM-side defaults remain client-side semantics unless a supported non-ORM writer is identified and a server-side default is explicitly approved. Migration backfill defaults needed to populate historical rows are separate from ongoing insert defaults. | Which external/direct-SQL writers, if any, are supported; whether timestamp/state/JSON defaults must also protect direct SQL or other services; historical migration default semantics versus current ORM behavior. |
| 3. PostgreSQL type mapping | ORM explicitly uses generic SQLAlchemy types. `DateTime(timezone=True)` is timezone-aware; trace table `created_at` declarations using bare `DateTime` are timezone-naive. ORM JSON is `JSON`, not `JSONB`. Raw migration `DATETIME` at `7757af5afe0a` is an evidenced PostgreSQL 16 incompatibility. | RESOLVED_BY_EVIDENCE | Preserve declared types in a PostgreSQL mapping: timezone-aware DateTime → `TIMESTAMP WITH TIME ZONE`; bare DateTime → `TIMESTAMP WITHOUT TIME ZONE`; JSON → PostgreSQL `JSON` (no evidence for `JSONB`); Text → `TEXT`; String(n) → `VARCHAR(n)`; Float → SQLAlchemy PostgreSQL floating representation (normally `DOUBLE PRECISION`); Integer → `INTEGER`; Boolean → `BOOLEAN`; integer autoincrement PKs use PostgreSQL identity/sequence behavior selected by the pinned SQLAlchemy/Alembic version. | Exact DDL emitted by the pinned dependency version has not been tested against PG16. Timestamp inputs for bare-DateTime trace fields and desired UTC/readback semantics need a product/runtime decision before relying on them. JSONB conversion is not justified by current evidence. |
| 4. Foreign-key delete/update actions | Metadata inspection covered all declared ORM FKs; neither ORM `ForeignKey` nor migration declarations specify `ondelete`/`onupdate`. PostgreSQL's default FK action in the absence of clause is `NO ACTION`. Several ORM relationships specify `cascade="all, delete-orphan"`; those affect ORM unit-of-work behavior and are not database cascades. Persistence repositories generally have no entity-delete API; memory has scoped deletion. | EXPLICIT_PRODUCT_DECISION_REQUIRED | If created literally from current declarations on PostgreSQL, use default `NO ACTION` for each FK; do not infer `CASCADE` from ORM relationship cascade. Existing ORM cascade behavior should remain an ORM behavior until separately changed. | Whether deletion of organizations/users/workspaces/projects/workflows/executions/ChangeSets should be blocked, set-null, or cascade at database level; behavior for direct SQL deletion; no repository tests establish complete parent deletion policy. Full FK inventory follows. |
| 5. Missing table creators and dependency order | Current metadata has 31 tables. The 23-revision chain has no creator for `projects`, `datasets`, `workflows`, `workflow_versions`, `workflow_executions`, `execution_traces`, or `capability_execution_traces`. `d14c1f2a9b31` alters datasets before a chain creator. `0001_persistence` conditionally creates users/executions/logs/reports based on table existence and fails to reconcile partial states. | RESOLVED_BY_EVIDENCE | Any future empty-database baseline must provide the runtime-required missing tables and their declared dependencies before dependent FKs/ALTERs. This is a confirmed statement of required completeness, not a selection of Alembic strategy or a claim that ORM metadata alone is the target. | Exact approved columns/defaults/indexes/constraints remain subject to the other decisions and PG16 validation. |
| 6. `0001_persistence` branches / existing schema handling | It checks only whether `users` and `executions` tables exist. If executions is absent it creates executions, validation_logs, and reports. If executions exists, it adds `user_id` only if missing. It does not ensure absent reports/logs/indexes or reconcile mismatched columns when only some objects exist. It creates email unique and an email index. | RESOLVED_BY_EVIDENCE | Treat the current revision as conditional legacy upgrade logic, not as a complete state-reconciliation routine or a complete first-install baseline. Preserve the observable branch behavior for supported older databases only after those states are inventoried. | Which local databases have applied it and whether partial schemas are supported. User-owned `.env`/tracked DB state is not classified as disposable; see companion inventory. |
| 7. Seed/reference data | No startup or migration seed script for default roles/permissions/memberships, risk-policy row, compliance policies, quotas, or default workspace was found. Persisted RBAC is wired in the container; with empty RBAC tables, permission lookups yield no grant. Risk repository falls back to domain defaults if no row exists. Quota service treats no quota as unlimited. Workspace requires owner; no seeded default workspace is required to start. Tests explicitly create RBAC and quota records. | EXPLICIT_PRODUCT_DECISION_REQUIRED | No evidence requires seed rows for process startup. Risk policy has a code fallback (`0.7`, `0.9`); no quota means unlimited; empty compliance list supplies no policy rows. Functional persisted authorization requires provisioning a role, permission links, and membership for users expected to receive grants. Do not invent a built-in seed set. | Define the first-owner/admin bootstrap/onboarding path and exact persisted permission catalogue. `risk_policies` has no singleton constraint; the container-wired repository calls `.first()` without ordering while a legacy repository orders by descending id. Decide whether to persist one risk policy and which selection rule applies. Decide if production requires finite quotas or compliance policies before access. Migration vs operator/bootstrap provisioning ownership is unresolved. |
| 8. ChangeSet and audit integrity canonicalization | `domain/changeset.py` constructs a mapping of immutable IDs, dataset/execution/workflow/version, before/after storage keys and hashes, plus items sorted by item ID with both snapshots. It excludes mutable status and lifecycle timestamps. `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)` then SHA-256 of UTF-8 bytes. `domain/audit.py` canonical payload contains id/scope/actor/action/resource/optional execution and ChangeSet IDs/sanitized metadata/`created_at.isoformat()`/previous hash, serialized with the same JSON options and SHA-256 UTF-8. Audit service chains previous hash per workspace under repository lock; verification checks previous hash and event hash. | RESOLVED_BY_EVIDENCE | Preserve these current canonicalization bytes and fields for compatibility. ChangeSet item order is by `id`, not insertion order. Audit event chain links by `previous_hash`; canonical `created_at` is ISO text. Do not change JSON normalization as part of schema provisioning. | Edge cases not proven include numeric non-finite values, nested custom objects, exact timezone equivalence across drivers, concurrent writers across DB backends, and whether all historical migration backfills match the current canonicalizer for every possible legacy value. These require targeted validation before changing behavior. |
| 9. Database operating contract | Alembic config points to `database/migrations`; `env.py` uses `Settings().database_url` and `Base.metadata`, and does not call `create_all()`. Production `Container` config sets `create_schema=False` and `require_current_revision=True`; this uses `ScriptDirectory.get_current_head()`, which expects one unambiguous head, and rejects a non-matching DB revision. API and worker both construct the container. Operator runbook says `alembic upgrade head`; Compose has no migration job. Migrations contain no extension setup. Owner/grant/schema ownership is not documented. | BLOCKED_BY_MISSING_EVIDENCE | Current code contract: migrations are an operator/deployment action before production API/worker startup; API and worker require exact repository current head and do not create tables in production. Current migration scripts declare no required extension. Do not treat Compose PostgreSQL health as schema readiness. | Who owns and runs the deployment migration job, schema/database owner and grants, extension policy, pinned image/dependency versions, backup schedule/restore responsibility, and supported single-head graph change process. No actual deployment exists. |
| 10. Validation contract for next phase | Existing tests establish SQLite ORM/application behavior and selected synthetic Alembic edges. No test or phase operation here establishes full empty PostgreSQL 16 bootstrap, full schema parity, API/worker production startup against a genuinely Alembic-provisioned PG database, or backup/restore. | RESOLVED_BY_EVIDENCE | The next authorized validation must be isolated and read-only until an explicit implementation authorization: empty PostgreSQL 16 clean provisioning; Alembic current/version state; table/column/type/default/index/unique/FK/sequence fingerprint against approved contract; API and worker startup with `create_schema=False`; representative reads/writes across every active table group; failure/transaction/recovery checks; and either backup/restore rehearsal or approved empty-database reprovision proof for first-install scope. | Exact test infrastructure, immutable PG image, test ownership, expected recovery point, and acceptance signatures must be approved before execution. No tests are authorized in this phase. |

## ORM Python-side default inventory

No ORM column in the inspected metadata declares `server_default`. The following are SQLAlchemy client defaults and are only applied when SQLAlchemy executes an INSERT that omits the column. “Candidate server default” means a separate design question for non-ORM writers, not a recommendation to add one. No default is being changed by this register.

| Table.column | ORM Python default | Classification | Evidence / qualification |
|---|---|---|---|
| `organizations.created_at` | UTC-aware `datetime.now(timezone.utc)` | Application-only default | Creation timestamp supplied by ORM insert path. |
| `compliance_policies.condition` | `dict` | Ambiguous / candidate DB default | Empty condition used by ORM inserts; raw SQL writer contract unknown. |
| `compliance_policies.enabled` | `True` | Ambiguous / candidate DB default | Migration has `server_default=true`; current ORM does not. Decide if DB writer must inherit enabled. |
| `memberships.created_at` | UTC-aware now | Application-only default | Same ORM-only limitation. |
| `users.created_at` | UTC-aware now | Application-only default | Same ORM-only limitation. |
| `workspaces.created_at` | UTC-aware now | Application-only default | `7757` raw creation path is invalid on PG16; later workspace migration omits some ORM fields/ownership history. |
| `channels.enabled` | `True` | Ambiguous / candidate DB default | Migration and ORM behavior should be field-compared; server default not established by current model. |
| `channels.created_at` | UTC-aware now | Application-only default | ORM insert path. |
| `projects.created_at` | UTC-aware now | Application-only default | No Alembic table creator. |
| `datasets.status` | `READY` | Ambiguous / candidate DB default | No creator migration; product lifecycle initial state must agree with ingestion code. |
| `datasets.metadata_json` | `dict` | Ambiguous / candidate DB default | No creator migration; empty JSON semantics. |
| `datasets.created_at` | UTC-aware now | Application-only default | No creator migration. |
| `sync_jobs.created_at` | UTC-aware now | Application-only default | ORM insert path. |
| `sync_attempts.external_product_id` | empty string | Application-only default | `20260916_02` declares the column non-nullable without a server default; ORM supplies the application default. |
| `sync_attempts.created_at` | UTC-aware now | Application-only default | ORM insert path. |
| `workflows.active_version` | `1.0` | Ambiguous / candidate DB default | No creator migration; workflow creation logic also initializes version state. |
| `workflows.status` | `DRAFT` | Ambiguous / candidate DB default | No creator migration; lifecycle state required by application. |
| `workflows.created_at` | UTC-aware now | Application-only default | No creator migration. |
| `workflow_versions.created_at` | UTC-aware now | Application-only default | No creator migration. |
| `workflow_executions.created_at` | UTC-aware now | Application-only default | No creator migration. |
| `executions.status` | `COMPLETED` | Ambiguous / candidate DB default | `0001` declares server default `completed` (lowercase), while current ORM default is `COMPLETED`; application also persists explicit states such as RUNNING/FAILED. This casing discrepancy requires decision. |
| `executions.created_at` | UTC-aware now | Application-only default | ORM default; migration base lacks this default distinction only when raw writer omits it. |
| `execution_traces.id` | UUID string | Application-only default | Trace record identity generated by ORM default; other records often require caller ID. |
| `execution_traces.created_at` | UTC-aware now; column is bare `DateTime` | Ambiguous / explicit product decision | Aware Python timestamp paired with timezone-naive SQL type. Define input normalization/readback semantics. |
| `capability_execution_traces.id` | UUID string | Application-only default | ORM default. |
| `capability_execution_traces.created_at` | UTC-aware now; column is bare `DateTime` | Ambiguous / explicit product decision | Same aware-value/naive-column concern. |
| `approvals.created_at` | UTC-aware now | Application-only default | `token_hash` migration uses a temporary server default to backfill old rows then removes it. |
| `risk_assessments.created_at` | UTC-aware now | Application-only default | ORM insert path. |
| `changesets.created_at` | UTC-aware now | Application-only default | Hash excludes lifecycle timestamps. |
| `audit_events.metadata_json` | `dict` | Ambiguous / candidate DB default | Migration/ORM writer parity needs confirmation for any direct writer; hash uses sanitized metadata. |
| `audit_events.created_at` | UTC-aware now | Application-only default | Timestamp is included as `isoformat()` in event commitment. |
| `data_lineage_events.input_refs_json` | `dict` | Ambiguous / candidate DB default | ORM empty-object default; raw writer support unknown. |
| `data_lineage_events.output_refs_json` | `dict` | Ambiguous / candidate DB default | ORM empty-object default; raw writer support unknown. |
| `data_lineage_events.created_at` | UTC-aware now | Application-only default | ORM insert path. |
| `risk_policies.high_risk_threshold` | `0.7` | Ambiguous / candidate DB default | Migration declares server default 0.7; repository falls back to domain default if no row. |
| `risk_policies.critical_risk_threshold` | `0.9` | Ambiguous / candidate DB default | Migration declares server default 0.9; repository fallback also supplies 0.9. |
| `reports.metadata_json` | `dict` | Ambiguous / candidate DB default | `0001` creates field but no equivalent ORM server default. |
| `channel_mappings.external_product_id` | empty string | Ambiguous / candidate DB default | `20260916_03` declares server default empty string. |
| `channel_mappings.last_synced_hash` | empty string | Ambiguous / candidate DB default | Migration declares server default empty string. |
| `channel_mappings.active` | `True` | Ambiguous / candidate DB default | Migration declares server default true. |
| `channel_mappings.created_at` | UTC-aware now | Application-only default | ORM insert path. |

Identifiers for most string-keyed entities are supplied by application/domain callers. UUID defaults above are the only model-level generated string IDs identified; `reports`, `validation_logs`, and `risk_policies` use integer autoincrement. Other fields have no ORM default and are required from their caller unless nullable.

## Foreign-key inventory

For every FK below, ORM and tracked migration declarations omit `ON DELETE` and `ON UPDATE`. The PostgreSQL default for a newly created constraint is `NO ACTION`; do not describe that as an evidenced product deletion policy. No repository-level entity delete API was found for these relations. ORM `delete-orphan` behavior is separately listed above and does not imply SQL-level cascade.

| FK column | References | Nullability | ORM relationship / repository behavior | Database delete action |
|---|---|---|---|---|
| `organization_quotas.organization_id` | `organizations.id` | NOT NULL | Quotas deleted as ORM children if organization relationship is loaded/deleted; no repository organization delete path found | Unspecified; PostgreSQL default NO ACTION |
| `compliance_policies.organization_id` | `organizations.id` | NOT NULL | Organization policy lookup; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `role_permissions.role_id` | `roles.id` | NOT NULL / PK member | ORM delete-orphan through role relation | Unspecified; PostgreSQL default NO ACTION |
| `role_permissions.permission_id` | `permissions.id` | NOT NULL / PK member | ORM delete-orphan through permission relation | Unspecified; PostgreSQL default NO ACTION |
| `memberships.user_id` | `users.id` | NOT NULL | Membership query by user/organization; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `memberships.organization_id` | `organizations.id` | NOT NULL | Membership child has no database cascade; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `memberships.role_id` | `roles.id` | NOT NULL | Membership query joins roles; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `workspaces.owner_id` | `users.id` | NOT NULL | ORM user→workspace delete-orphan; production deletion semantics untested | Unspecified; PostgreSQL default NO ACTION |
| `workspaces.organization_id` | `organizations.id` | NULLABLE | Optional organization membership; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `channels.workspace_id` | `workspaces.id` | NOT NULL | Owner/workspace scoped channel lookup; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `projects.workspace_id` | `workspaces.id` | NOT NULL | ORM workspace→project delete-orphan; project access scoped by workspace | Unspecified; PostgreSQL default NO ACTION |
| `datasets.project_id` | `projects.id` | NOT NULL | ORM project→dataset delete-orphan; no repository hard-delete path found | Unspecified; PostgreSQL default NO ACTION |
| `sync_jobs.workspace_id` | `workspaces.id` | NOT NULL | Workspace isolation and idempotency scope | Unspecified; PostgreSQL default NO ACTION |
| `sync_jobs.dataset_id` | `datasets.id` | NOT NULL | Sync input dataset | Unspecified; PostgreSQL default NO ACTION |
| `sync_jobs.channel_id` | `channels.id` | NOT NULL | Sync target channel | Unspecified; PostgreSQL default NO ACTION |
| `sync_attempts.sync_job_id` | `sync_jobs.id` | NOT NULL | Attempt history; parent hard-delete behavior not found | Unspecified; PostgreSQL default NO ACTION |
| `workflows.project_id` | `projects.id` | NOT NULL | ORM project→workflow delete-orphan | Unspecified; PostgreSQL default NO ACTION |
| `workflow_versions.workflow_id` | `workflows.id` | NOT NULL | ORM workflow→version delete-orphan; versions are immutable snapshots in behavior tests | Unspecified; PostgreSQL default NO ACTION |
| `workflow_executions.workflow_id` | `workflows.id` | NOT NULL | ORM workflow→execution delete-orphan; execution history/state semantics | Unspecified; PostgreSQL default NO ACTION |
| `workflow_executions.dataset_id` | `datasets.id` | NULLABLE | Optional selected dataset; migration adds nullable FK/index | Unspecified; PostgreSQL default NO ACTION |
| `executions.user_id` | `users.id` | NULLABLE | Optional actor attribution; no repository delete path found | Unspecified; PostgreSQL default NO ACTION |
| `executions.dataset_id` | `datasets.id` | NULLABLE | Optional quality dataset; migration adds nullable FK/index | Unspecified; PostgreSQL default NO ACTION |
| `agent_memory.workspace_id` | `workspaces.id` | NOT NULL | Scope filter and workspace index; explicit repository row deletion only | Unspecified; PostgreSQL default NO ACTION |
| `agent_memory.user_id` | `users.id` | NOT NULL | Scope filter and user index; explicit repository row deletion only | Unspecified; PostgreSQL default NO ACTION |
| `validation_logs.execution_id` | `executions.id` | NOT NULL | ORM execution→logs delete-orphan | Unspecified; PostgreSQL default NO ACTION |
| `execution_traces.execution_id` | `executions.id` | NOT NULL | ORM execution→traces delete-orphan | Unspecified; PostgreSQL default NO ACTION |
| `capability_execution_traces.workflow_execution_id` | `workflow_executions.id` | NOT NULL | ORM workflow execution→traces delete-orphan | Unspecified; PostgreSQL default NO ACTION |
| `approvals.execution_id` | `workflow_executions.id` | NOT NULL | Approval lifecycle tied to workflow execution | Unspecified; PostgreSQL default NO ACTION |
| `approvals.changeset_id` | `changesets.id` | NOT NULL | Approval tied to immutable ChangeSet | Unspecified; PostgreSQL default NO ACTION |
| `risk_assessments.execution_id` | `workflow_executions.id` | NOT NULL | Risk decision history tied to workflow execution | Unspecified; PostgreSQL default NO ACTION |
| `changesets.dataset_id` | `datasets.id` | NOT NULL | Mutation artifact ownership/integrity | Unspecified; PostgreSQL default NO ACTION |
| `changesets.execution_id` | `workflow_executions.id` | NOT NULL | Mutation provenance | Unspecified; PostgreSQL default NO ACTION |
| `changesets.workflow_id` | `workflows.id` | NOT NULL | Workflow/version provenance | Unspecified; PostgreSQL default NO ACTION |
| `changeset_items.changeset_id` | `changesets.id` | NOT NULL | ORM ChangeSet→item delete-orphan; integrity order by item ID | Unspecified; PostgreSQL default NO ACTION |
| `data_lineage_events.dataset_id` | `datasets.id` | NOT NULL | Lineage provenance | Unspecified; PostgreSQL default NO ACTION |
| `data_lineage_events.execution_id` | `workflow_executions.id` | NOT NULL | Lineage provenance | Unspecified; PostgreSQL default NO ACTION |
| `data_lineage_events.workflow_id` | `workflows.id` | NOT NULL | Lineage provenance | Unspecified; PostgreSQL default NO ACTION |
| `audit_events.workspace_id` | `workspaces.id` | NOT NULL | Per-workspace audit chain; no delete path found | Unspecified; PostgreSQL default NO ACTION |
| `audit_events.actor_id` | `users.id` | NOT NULL | Actor attribution; no delete path found | Unspecified; PostgreSQL default NO ACTION |
| `audit_events.execution_id` | `workflow_executions.id` | NULLABLE | Optional execution provenance | Unspecified; PostgreSQL default NO ACTION |
| `audit_events.changeset_id` | `changesets.id` | NULLABLE | Optional ChangeSet provenance | Unspecified; PostgreSQL default NO ACTION |
| `reports.execution_id` | `executions.id` | NOT NULL | ORM execution→reports delete-orphan | Unspecified; PostgreSQL default NO ACTION |
| `channel_mappings.channel_id` | `channels.id` | NOT NULL | Mapping lookup by channel; no hard-delete path found | Unspecified; PostgreSQL default NO ACTION |

## First-install dependency order (not a migration plan)

The following order is a topological ordering of current ORM foreign-key prerequisites. It is not a choice of Alembic lineage, does not resolve all required schema details, and does not assert that all tables should be seeded. Tables without dependencies may be created in any order within their tier. Indexes and unique constraints should be created with or after each table according to the final approved contract.

| Tier | Tables in a valid prerequisite order | Current Alembic creation evidence | Fresh baseline implication |
|---|---|---|---|
| 0 | `organizations`, `users`, `roles`, `permissions`, `risk_policies` | organizations/roles/permissions in `20260916_04`; risk_policies in `20230912_01`; users conditional in `0001`; no complete fresh baseline because the existing graph has contradictions | Create principal/lookup tables first. |
| 1 | `workspaces` | `7757af5afe0a` attempts raw PG-invalid creation; `fcbc1a52044c` later duplicates; `20260916_04` adds organization_id | Must be created once with final owner/organization columns and reviewed nullability/FKs. |
| 2 | `memberships`, `organization_quotas`, `compliance_policies`, `projects`, `channels`, `agent_memory`, `role_permissions` | Membership/quota/compliance/channels/agent memory/role_permissions have creators; projects missing | These follow organizations/users/roles/permissions/workspaces; no creator exists for projects. |
| 3 | `datasets`, `workflows`, `executions`, `sync_jobs` | Datasets/workflows missing; executions created conditionally in `0001`; sync jobs created but require dataset/channel/workspace | Projects precede datasets/workflows; users and datasets precede executions; sync jobs follow workspace, datasets and channels. |
| 4 | `workflow_versions`, `workflow_executions`, `sync_attempts`, `channel_mappings`, `validation_logs`, `reports`, `execution_traces` | Workflow versions/executions/execution traces missing; sync attempts/channel mappings have creators; logs/reports conditional in `0001` | All referenced parents must exist; workflow executions follow workflows/datasets; execution traces, logs and reports follow executions. |
| 5 | `risk_assessments`, `changesets` | Risk/ChangeSet creators exist but depend on workflow executions, datasets, workflows, and executions | Create after all referenced execution and dataset/workflow parents. |
| 6 | `approvals`, `changeset_items`, `data_lineage_events`, `audit_events`, `capability_execution_traces` | Approval/item/lineage/audit creators exist; capability traces missing | Approvals follow ChangeSets and workflow executions; items follow ChangeSets; lineage/audit/traces follow their dataset/workflow/execution references. |

Every table’s exact columns, types, defaults, primary keys, indexes, and unique constraints are in [CANONICAL_SCHEMA_RECONCILIATION.md](CANONICAL_SCHEMA_RECONCILIATION.md) and [FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md](FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md). The active Alembic chain can create some tables, but **cannot create the full 31-table schema from empty**. Seven current ORM tables lack a creator. This is a factual gap, not authorization to create a baseline.

### Per-table creator and constraint matrix

“Columns” lists the complete current ORM column names; nullability and type are in the linked field-level inventory. “Alembic creator” records whether any tracked revision has a `create_table` path, including conditional paths; an ALTER of a nonexistent table is not counted as a creator. Every table is a **candidate required table for a complete baseline**, because it is part of active ORM metadata; the final approved target still needs the open decisions above.

| Table | Prerequisite tables | Current Alembic creator | Columns from ORM metadata | ORM indexes / unique constraints | Can current history create from empty? | New baseline must create? |
|---|---|---|---|---|---|---|
| `organizations` | — | `20260916_04` | id, name, created_at | `ix_organizations_created_at` | No: earlier chain fails first; table creator is after conflicting workspace history | Yes, pending contract |
| `users` | — | `0001_persistence` conditional on table absent | id, email, display_name, created_at | `ix_users_created_at`; unique index `ix_users_email` | Partial only; branch does not reconcile partial schema | Yes, pending contract |
| `roles` | — | `20260916_04` | id, name, description | unique name | No: chain prerequisite/ordering failures | Yes, pending contract |
| `permissions` | — | `20260916_04` | id, resource, action | unique `(resource, action)` | No: chain prerequisite/ordering failures | Yes, pending contract |
| `risk_policies` | — | `20230912_01` | id, high_risk_threshold, critical_risk_threshold | none | No: chain fails earlier | Yes, pending contract |
| `workspaces` | users; optional organizations | `7757af5afe0a` conditional raw create, then conflicting unconditional `fcbc1a52044c`; `20260916_04` alters | id, owner_id, organization_id, name, created_at | owner/organization/created indexes | No: raw `DATETIME` fails and duplicate creator conflicts | Yes, once, pending contract |
| `memberships` | users, organizations, roles | `20260916_04` | id, user_id, organization_id, role_id, created_at | unique `(user_id, organization_id, role_id)`; user/org/role/created indexes | No: chain fails earlier | Yes, pending contract |
| `organization_quotas` | organizations | `20260922_01` | id, organization_id, dimension, limit | unique `(organization_id, dimension)`; organization index | No: chain fails earlier | Yes, pending contract |
| `compliance_policies` | organizations | `20260923_01` | id, organization_id, name, resource, action, condition, reason, enabled | unique `(organization_id, name)`; organization index | No: chain fails earlier | Yes, pending contract |
| `projects` | workspaces | **None found** | id, workspace_id, name, description, created_at | workspace index | No | Yes, pending contract |
| `channels` | workspaces | `20260916_01` | id, workspace_id, channel_type, name, credentials_encrypted, enabled, created_at | unique `(workspace_id, channel_type, name)`; workspace/created indexes | No: chain fails earlier | Yes, pending contract |
| `agent_memory` | workspaces, users | `c13a7e91d204` conditional on table absent | id, workspace_id, user_id, memory_type, memory_key, value_json, created_at, expires_at | workspace/user/expiry and `(workspace_id,user_id,memory_type,memory_key)` indexes | No: prerequisite tables/chain failures | Yes, pending contract |
| `role_permissions` | roles, permissions | `20260916_04` | role_id, permission_id | composite PK `(role_id, permission_id)` plus unique constraint over same pair | No: chain fails earlier | Yes, pending contract; confirm redundant unique |
| `datasets` | projects | **None found**; first referenced/altered by `d14c1f2a9b31` | id, project_id, name, source_type, filename, file_format, size_bytes, content_hash, storage_key, row_count, column_count, status, metadata_json, created_at | project/content_hash/status indexes | No | Yes, pending contract |
| `workflows` | projects | **None found** | id, project_id, name, active_version, status, created_at | project index | No | Yes, pending contract |
| `executions` | optional users; optional datasets | `0001_persistence` conditional on table absent; `f3a4b5c6d7e8` adds dataset_id | id, user_id, dataset_id, category, source_hash, rule_version, health_score, status, created_at, requirement_json, plan_json, planner_version | user/dataset/category/source_hash/created indexes | Partial only; table create branch is conditional and later ALTER needs datasets | Yes, pending contract |
| `sync_jobs` | workspaces, datasets, channels | `20260916_02` | id, workspace_id, dataset_id, channel_id, idempotency_key, status, error, created_at | unique `(workspace_id, idempotency_key)`; workspace/dataset/channel/status/created indexes | No: datasets missing and chain fails earlier | Yes, pending contract |
| `workflow_versions` | workflows | **None found** | id, workflow_id, version, plan_json, created_at | unique `(workflow_id, version)`; workflow index | No | Yes, pending contract |
| `workflow_executions` | workflows; optional datasets | **None found**; `e2f3a4b5c6d7` only alters | id, workflow_id, dataset_id, workflow_version, status, inputs_json, outputs_json, error, started_at, finished_at, created_at | workflow/dataset/created indexes | No | Yes, pending contract |
| `sync_attempts` | sync_jobs | `20260916_02` | id, sync_job_id, attempt_number, status, request_hash, external_product_id, error, created_at | unique `(sync_job_id, attempt_number)`; job/status/created indexes | No: parent chain fails | Yes, pending contract |
| `channel_mappings` | channels | `20260916_03` | id, channel_id, canonical_product_id, channel_type, external_product_id, last_synced_hash, active, created_at | unique `(channel_id, canonical_product_id)`; channel/product/created indexes | No: chain fails earlier | Yes, pending contract |
| `validation_logs` | executions | `0001_persistence` conditional within executions-absent branch | id, execution_id, row_number, field, code, message, severity | execution index | Partial only; not created if executions already exists | Yes, pending contract |
| `reports` | executions | `0001_persistence` conditional within executions-absent branch | id, execution_id, format, path, metadata_json | execution index | Partial only; not created if executions already exists | Yes, pending contract |
| `execution_traces` | executions | **None found** | id, execution_id, capability_id, capability_version, status, inputs_json, outputs_json, started_at, finished_at, duration_ms, error, created_at | execution index | No | Yes, pending contract |
| `capability_execution_traces` | workflow_executions | **None found** | id, workflow_execution_id, capability_id, capability_version, status, inputs_json, outputs_json, started_at, finished_at, duration_ms, error, created_at | workflow_execution index | No | Yes, pending contract |
| `risk_assessments` | workflow_executions | `20230912_03` | id, execution_id, risk_score, confidence_score, approval_required, created_at | execution index | No: workflow_executions creator absent | Yes, pending contract |
| `changesets` | datasets, workflow_executions, workflows | `20260914_01`; `20260926_01` and `20260928_01` alter/backfill integrity | id, dataset_id, execution_id, workflow_id, workflow_version, before_storage_key, before_content_hash, after_storage_key, after_content_hash, integrity_hash, status, created_at, applied_at, rolled_back_at | dataset/execution/workflow/status/created indexes | No: parent creators absent | Yes, pending contract |
| `approvals` | workflow_executions, changesets | `20230912_01`; `20230912_02`, `20230912_04`, `20260914_02` alter | approval_id, execution_id, changeset_id, risk_score, confidence_score, requested_by, created_at, expires_at, decision, token_hash | execution/changeset indexes | No: prerequisite tables/chain fail | Yes, pending contract |
| `changeset_items` | changesets | `20260914_01` | id, changeset_id, entity, record_id, before_snapshot, after_snapshot | changeset index | No: parent creators absent | Yes, pending contract |
| `data_lineage_events` | datasets, workflow_executions, workflows | `20260914_03` | id, dataset_id, execution_id, workflow_id, workflow_version, capability_id, capability_version, event_type, input_refs_json, output_refs_json, created_at | dataset/execution/workflow/created indexes | No: parent creators absent | Yes, pending contract |
| `audit_events` | workspaces, users; optional workflow_executions, changesets | `20260914_03` | id, workspace_id, actor_id, action, resource_type, resource_id, execution_id, changeset_id, metadata_json, created_at, previous_hash, event_hash | workspace/actor/resource/execution/changeset/created indexes; unique event_hash index | No: parent creators absent and chain fails earlier | Yes, pending contract |

The list contains all 31 current ORM tables. Exact nullability and SQLAlchemy types remain in the referenced schema inventory. The “new baseline must create” column means the table belongs to the currently evidenced persistence surface; each one remains subject to approved product/schema decisions and is not a DDL authorization.

## Seed and operating conclusions

- **RBAC:** startup does not query role data, but the production container injects `RBACRepository` into authorization. Empty membership/permission tables mean no persisted permission grant. The exact first-admin/role/permission seed and provisioning owner need a product/operations decision. `ROLE_PERMISSIONS` is a compatibility fallback only when the repository is not configured; current container wiring configures it.
- **Risk:** no risk-policy row is required for startup or basic risk evaluation because repository code returns `RiskPolicy()` defaults (`0.7`, `0.9`) when no row exists. Persisted override is optional. The container-wired repository uses unordered `.first()` and schema does not enforce a singleton; choose one-row provisioning/selection semantics before relying on persisted overrides.
- **Quotas:** no quota row means unlimited for that organization/dimension by explicit `QuotaService` behavior. Which production quotas to configure is a product decision; no seed is necessary for startup.
- **Compliance:** no default organization policy seed was found. Policies are evaluated from rows; required baseline policy set is a product/governance decision.
- **Default workspace:** no application startup seed exists; workspaces require an owner. Workspace/user onboarding must provision owned rows through an authorized application path.
- **Migrations:** `docs/operator/database-migration.md` directs an operator to run `alembic upgrade head`; Compose defines no migration service. Current production container disables `create_all()` and requires the current repository revision. The current wiring obtains `ScriptDirectory.get_current_head()` and assumes exactly one unambiguous head. No owner role/grants/extensions/migration-job identity or production deployment exists.

## Gate — historical discovery snapshot, superseded 2026-10-02

Six of the ten decision topics have their repository facts resolved: email lookup/uniqueness, generic PG type mapping from declared SQLAlchemy types, missing creator facts/dependency requirements, `0001`'s branch behavior, the current integrity canonicalization algorithms, and the next-phase validation evidence list. Four remain because choosing semantics or operations would exceed repository evidence: ongoing default policy, intended FK delete behavior, required first-install seed/admin set, and database operational ownership/grants/deployment lifecycle.

```text
SCHEMA_DECISIONS_RESOLVED = 6
SCHEMA_DECISIONS_REMAINING = 4
CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
MIGRATION_STRATEGY = UNDECIDED
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```

## Final policy classification — historical owner-policy snapshot, superseded by final reconciliation

These classifications preserve the observed application contract; they do **not** authorize DDL. “Must remain application default” means keep the current application-side default behavior. It does not assert that adding a matching database default is unsafe. “Both required” is supported by a current ORM default and a persistent server default in migration history. “Owner decision required” means the code/history conflict or the permitted writer contract is insufficient to select a target rule.

### All 41 ORM Python defaults

| Classification | Fields | Evidence and limit |
|---|---|---|
| MUST_REMAIN_APPLICATION_DEFAULT | `organizations.created_at`; `compliance_policies.condition`; `memberships.created_at`; `users.created_at`; `workspaces.created_at`; `channels.enabled`, `channels.created_at`; `projects.created_at`; `datasets.status`, `datasets.metadata_json`, `datasets.created_at`; `sync_jobs.created_at`; `sync_attempts.created_at`, `sync_attempts.external_product_id`; `workflows.active_version`, `workflows.status`, `workflows.created_at`; `workflow_versions.created_at`; `workflow_executions.created_at`; `executions.created_at`; `execution_traces.id`, `execution_traces.created_at`; `capability_execution_traces.id`, `capability_execution_traces.created_at`; `approvals.created_at`; `risk_assessments.created_at`; `changesets.created_at`; `audit_events.metadata_json`, `audit_events.created_at`; `data_lineage_events.input_refs_json`, `data_lineage_events.output_refs_json`, `data_lineage_events.created_at`; `reports.metadata_json`; `channel_mappings.created_at` | These are current SQLAlchemy-side defaults. Current ORM behavior and repository paths establish the application default behavior to preserve. No supported direct-SQL writer or test establishes that omitting these fields outside ORM is supported; therefore this classification does not require a server default. For audit timestamps included in hashes and trace timestamps stored in naive columns, application-level value semantics still need to be preserved and PostgreSQL round-trip behavior separately validated. |
| BOTH_REQUIRED | `compliance_policies.enabled`; `risk_policies.high_risk_threshold`; `risk_policies.critical_risk_threshold`; `channel_mappings.external_product_id`; `channel_mappings.last_synced_hash`; `channel_mappings.active` | Current ORM defaults and tracked migrations both provide persistent server defaults for these same values. Preserve both observed behaviors unless an owner approves a contract change. The migration defaults are evidence of schema behavior, not evidence that arbitrary external writers are supported. |
| SHOULD_BE_DATABASE_SERVER_DEFAULT | None established | Repository evidence does not identify a field for which a server-only default is the correct contract. Moving an application default exclusively to PostgreSQL could change when the value becomes available to application logic. |
| OWNER_DECISION_REQUIRED | `executions.status` | ORM default is uppercase `COMPLETED`; migration `0001_persistence` records lowercase `completed`. Application code also explicitly uses multiple lifecycle states. Neither migration history nor existing tests settle whether case normalization is intended. Resolve before choosing a canonical database default. |

This historical snapshot accounts for 34 MUST_REMAIN_APPLICATION_DEFAULT, 6 BOTH_REQUIRED, 0 SHOULD_BE_DATABASE_SERVER_DEFAULT, and 1 OWNER_DECISION_REQUIRED field. Its status classifications are superseded; the migration evidence for `sync_attempts.external_product_id` is corrected above and in the current reconciliation section.

### All 43 foreign keys

No FK is classified `DB_CASCADE_REQUIRED`, `DB_RESTRICT_OR_NO_ACTION_REQUIRED`, or `DB_SET_NULL_REQUIRED`: those are product deletion policies, and the repository does not establish them. For all 43, current ORM and migration declarations omit `ondelete`/`onupdate`; a newly created PostgreSQL constraint would therefore use its engine default, but that is not proof that the product intends a deletion policy. No repository-level parent deletion behavior test settles this question.

| Classification | FK fields | Evidence and limit |
|---|---|---|
| ORM_ONLY_CASCADE | `organization_quotas.organization_id`; `role_permissions.role_id`, `role_permissions.permission_id`; `workspaces.owner_id`; `projects.workspace_id`; `datasets.project_id`; `workflows.project_id`; `workflow_versions.workflow_id`; `workflow_executions.workflow_id`; `validation_logs.execution_id`; `execution_traces.execution_id`; `capability_execution_traces.workflow_execution_id`; `changeset_items.changeset_id`; `reports.execution_id` | Existing ORM relationships use `delete-orphan`/unit-of-work cascade. This describes ORM behavior only; current database declarations do not request `ON DELETE CASCADE`. No evidence justifies translating the ORM behavior into a database action. |
| OWNER_DECISION_REQUIRED | `compliance_policies.organization_id`; `memberships.user_id`, `memberships.organization_id`, `memberships.role_id`; `workspaces.organization_id`; `channels.workspace_id`; `sync_jobs.workspace_id`, `sync_jobs.dataset_id`, `sync_jobs.channel_id`; `sync_attempts.sync_job_id`; `workflow_executions.dataset_id`; `executions.user_id`, `executions.dataset_id`; `agent_memory.workspace_id`, `agent_memory.user_id`; `approvals.execution_id`, `approvals.changeset_id`; `risk_assessments.execution_id`; `changesets.dataset_id`, `changesets.execution_id`, `changesets.workflow_id`; `data_lineage_events.dataset_id`, `data_lineage_events.execution_id`, `data_lineage_events.workflow_id`; `audit_events.workspace_id`, `audit_events.actor_id`, `audit_events.execution_id`, `audit_events.changeset_id`; `channel_mappings.channel_id` | No FK-level delete/update action is declared. Repository code either has no parent-delete operation, explicitly scopes row deletion, or preserves audit/execution/provenance records. These facts do not determine the required database policy for hard deletion or direct SQL. Decide retention, anonymization, and deletion semantics before schema repair. |
| DB_CASCADE_REQUIRED / DB_RESTRICT_OR_NO_ACTION_REQUIRED / DB_SET_NULL_REQUIRED | None established | Existing evidence is insufficient to require any one database action. A nullable FK alone does not prove `SET NULL`; PostgreSQL's default `NO ACTION` is not a product decision. |

Count check: 14 ORM_ONLY_CASCADE plus 29 OWNER_DECISION_REQUIRED equals the inspected 43 declared FKs. No delete-action tests cover the complete parent-child graph; existing relationship tests protect selected ORM behavior only.

### First-install seed policy

| Record family | Repository evidence | Classification for first install |
|---|---|---|
| Organizations and users | Created through application/repository operations; no first-owner creation path or seed artifact found. | OWNER_DECISION_REQUIRED for bootstrap identity and operator procedure; do not fabricate seed users or organizations. |
| Roles, permissions, role-permission links, memberships | Production container wires persisted RBAC. Empty records produce no persisted grant; fallback constants apply only when no repository is injected. | REQUIRED before granting governed access; exact catalogue, initial administrator, and provisioning owner are OWNER_DECISION_REQUIRED. Not shown to be startup-required. |
| Quotas | No quota row means unlimited in current service behavior. | No seed required to start; owner decision required if a finite production quota is mandatory. |
| Risk policies | Missing row falls back to `0.7`/`0.9`; table is used by the repository, but a row is not required for the fallback. Multiple rows have ambiguous selection in the container-wired path. | No seed required for fallback behavior; persisted seed cardinality and selection require OWNER_DECISION_REQUIRED. |
| Compliance policies | No default policy seed or startup invariant found. | No seed required to start; baseline governance policy set is OWNER_DECISION_REQUIRED. |
| Demo/default workspace | No default workspace seed; a workspace requires an owner. | Not required for startup; do not create demo records without product approval. |
| Other startup-required records | Startup requires the expected schema/revision, not a discovered application data seed. | No data seed established as startup-required. First-owner onboarding remains unresolved. |

The repository does not establish where an approved seed should run (migration, one-shot bootstrap command, or operator workflow). Do not place seed data in a migration by assumption.

### Database operating contract: evidenced versus undecided

**Established in repository:** development container wiring can invoke ORM `create_all()`; production container wiring disables it and requires the single current Alembic head; API and worker need the expected schema/revision before startup; Alembic targets `Base.metadata`; operator documentation directs `alembic upgrade head`; Compose does not run that command; tracked migration scripts do not declare extension setup.

**Not established:** actual owner/operator and identity for migration execution; database/schema ownership and grants; extension policy; immutable PostgreSQL image and dependency pin for deployment; maintenance/locking window; backup cadence, retention, restore responsibility and recovery point; first-install provisioning order; how local persistent states are preserved or transitioned. Therefore `DATABASE_OPERATING_CONTRACT = OWNER_DECISION_REQUIRED`, not defined. No database or deployment behavior was validated in this review.

## Closure gate — historical discovery snapshot, superseded 2026-10-02
The original ten decision groups remain six resolved by repository evidence and four requiring an owner decision or external validation. The unresolved groups are ongoing default policy, FK deletion policy, first-install seed/bootstrap policy, and database operational ownership/lifecycle. Local persistent state disposition is an additional incomplete readiness item, not a reclassification of those ten topics.

```text
DEFAULT_POLICY_STATUS = OWNER_DECISION_REQUIRED
FK_POLICY_STATUS = OWNER_DECISION_REQUIRED
SEED_POLICY_STATUS = OWNER_DECISION_REQUIRED
DATABASE_OPERATING_CONTRACT = OWNER_DECISION_REQUIRED
LOCAL_STATE_DISPOSITION = INCOMPLETE

CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
SCHEMA_DECISIONS_RESOLVED = 6
SCHEMA_DECISIONS_REMAINING = 4

MIGRATION_STRATEGY = UNDECIDED
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```


## Owner policy application — 2026-10-02 (superseded by final reconciliation)

This section supersedes prior provisional classifications above where they conflict with the explicit owner policies supplied on 2026-10-02. It records decisions, not implementation.

- **Defaults:** all 41 defaults are application-owned; do not add server defaults except database identity/sequence invariants. The old lowercase `executions.status` server default is not part of the target; canonical app value is uppercase `COMPLETED`. Omitting that field in direct SQL changes from the historical migration behavior; this is an explicit runtime exception. See [`FIELD_DEFAULT_POLICY_MATRIX.md`](FIELD_DEFAULT_POLICY_MATRIX.md).
- **Foreign keys:** all 43 default to `NO ACTION`; ORM cascades are not copied to DDL. The three candidate exceptions (`organization_quotas.organization_id`, `role_permissions.role_id`, `role_permissions.permission_id`) remain `OWNER_DECISION_REQUIRED`; until confirmed, no cascade is part of the target. See [`FK_DELETE_POLICY_MATRIX.md`](FK_DELETE_POLICY_MATRIX.md).
- **Seeds:** `SYSTEM_SEED=YES` for required RBAC roles, permissions and links; no initial admin, credentials, memberships, tenant records, demo data, default workspace, arbitrary quota, risk policy, or compliance policy. Risk uses code fallback; empty compliance policy list currently allows. First-user/organization onboarding is a separate operator action. See [`SYSTEM_SEED_CONTRACT.md`](SYSTEM_SEED_CONTRACT.md).
- **Operations:** selected model is a dedicated Alembic migration job before application/API/workers; automatic startup migrations are prohibited. Existing deployment wiring and clean-install migration history are not repaired by this decision. See [`DATABASE_OPERATING_CONTRACT.md`](DATABASE_OPERATING_CONTRACT.md).
- **Local state:** preserve tracked SQLite files and persistent Compose volumes until inspected; keep `aeop-postgres16-verify` available for separately authorized PostgreSQL validation. See [`LOCAL_DATABASE_DISPOSITION.md`](LOCAL_DATABASE_DISPOSITION.md).

```text
DEFAULT_POLICY_STATUS = RESOLVED_BY_OWNER_POLICY
FK_POLICY_STATUS = RESOLVED_BY_OWNER_POLICY_WITH_3_EXCEPTIONS
SEED_POLICY_STATUS = RESOLVED_BY_OWNER_POLICY
DATABASE_OPERATING_CONTRACT = DEFINED; DEPLOYMENT DETAILS UNIMPLEMENTED
LOCAL_STATE_DISPOSITION = POLICY_DEFINED; PERSISTENT CONTENTS UNINSPECTED
CANONICAL_TARGET_SCHEMA = NOT_YET_DEFINED
SCHEMA_DECISIONS_REMAINING = 3
MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB (selected operating model)
IMPLEMENTATION_AUTHORIZATION = NOT_AUTHORIZED
```

## FINAL TARGET-SCHEMA / MIGRATION-HISTORY RECONCILIATION — CURRENT

This is the current decision record and supersedes all earlier status blocks in this file. See [`TARGET_SCHEMA_RECONCILIATION.md`](TARGET_SCHEMA_RECONCILIATION.md) for the ten discrepancy classifications and schema-versus-migration-path boundary.

- All three FK cascade candidates are **RESOLVED_BY_POLICY** to `NO ACTION`; current repository/runtime evidence does not require a database CASCADE.
- All seven persistent historical server-default differences are classified as **INTENTIONAL_BEHAVIOR_CHANGE** under the application-owned-default policy. `sync_attempts.external_product_id` has no historical migration server default and is not one of the seven. The temporary approval-token backfill default is not persistent and is excluded.
- The ten migration-history discrepancies are classified as migration debt/schema installation gaps with canonical target definitions supplied by the ORM/runtime inventory; none remains an unresolved target-schema decision.
- The canonical logical target is defined for the 31-table surface. Strategy D is implemented as a single-head baseline (`20261002_01`); the 23 former revisions are preserved in the inactive archive. This is static evidence only, not PostgreSQL 16 validation.
- The dedicated migration-job model remains selected. Local persistent files and volumes remain preserved until inspected; there is no production baseline to preserve.

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
```
