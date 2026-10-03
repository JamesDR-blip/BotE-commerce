# Canonical Schema Contract

**Purpose:** owner-approved logical contract for first PostgreSQL 16 provisioning. This document records target decisions. Alembic implementation status and static validation are recorded in [`MIGRATION_REPAIR_IMPLEMENTATION.md`](MIGRATION_REPAIR_IMPLEMENTATION.md); no PostgreSQL database operation has been performed.

## Authority and scope

There has never been production or staging deployment or production data. There is no historical production schema to preserve. The canonical logical model is the current reconciled 31-table persistence surface in [`CANONICAL_SCHEMA_RECONCILIATION.md`](CANONICAL_SCHEMA_RECONCILIATION.md) and [`FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md`](FIRST_PRODUCTION_PROVISIONING_ASSESSMENT.md), constrained by runtime behavior and the policies in this contract. Existing local DBs are a separate preservation/inventory concern.

The owner policy sets semantics; the former 23-revision active history had known missing table creators, duplicate/conflicting workspace history, and a PostgreSQL 16-incompatible raw `DATETIME` operation in `7757af5afe0a`. Strategy D now replaces that active path with the `20261002_01` baseline and preserves the former revisions in an inactive archive. Structural alignment is statically checked; PostgreSQL-generated DDL and runtime behavior remain unverified.

## Canonical rules

- **Columns and logical fields:** use the current reconciled ORM/runtime table inventory as the target evidence. Preserve application-observed names, types, nullability, uniqueness, indexes, and lifecycle fields. Any ORM/migration conflict must be explicitly reconciled in the schema repair design; do not assume the historical migration wins solely by age.
- **Defaults:** all 41 Python defaults remain application-owned. Do not add server defaults for them. The only database-generated defaults are identity/sequence behavior for integer autoincrement primary keys. Full per-field decisions are in [`FIELD_DEFAULT_POLICY_MATRIX.md`](FIELD_DEFAULT_POLICY_MATRIX.md).
- **Explicit runtime exception:** canonical `executions.status` application default is uppercase `COMPLETED`; do not preserve the old lowercase `completed` server default. Raw SQL that omitted the value under a historically migrated schema may therefore behave differently. No production data exists; local DBs must be classified and preserved before any transition.
- **Foreign keys:** `NO ACTION` is the selected policy for all 43 FKs. The three candidate owned-child exceptions were reviewed; no repository/runtime behavior requires a database cascade, so they are resolved by policy without exceptions. See [`FK_DELETE_POLICY_MATRIX.md`](FK_DELETE_POLICY_MATRIX.md).
- **No demo/sample data, admin user, or credentials** in schema migrations. System reference rows are limited to the required RBAC catalogue described in [`SYSTEM_SEED_CONTRACT.md`](SYSTEM_SEED_CONTRACT.md).
- **Operations:** a dedicated migration job runs Alembic before API/application and worker startup. Applications do not migrate schema automatically.

## Status

The canonical logical target is defined for the 31-table ORM/runtime surface. Defaults, FK actions, seed policy, and operating model are closed at contract level. The former history's clean-install defects and omissions are addressed in the active baseline; PostgreSQL-rendered DDL and runtime validation remain unperformed and require separate authorization.

```text
CANONICAL_TARGET_SCHEMA = DEFINED
SCHEMA_DECISIONS_REMAINING = 0
MIGRATION_STRATEGY = DEDICATED_MIGRATION_JOB
MIGRATION_GRAPH_STATUS = IMPLEMENTED_STATICALLY
POSTGRESQL_16_VALIDATION = NOT_AUTHORIZED
```
