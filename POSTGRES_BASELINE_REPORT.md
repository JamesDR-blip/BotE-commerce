# PostgreSQL Baseline Report

**Verification date:** 2026-10-02  
**Scope:** read-only local environment and repository evidence review. No database was created or contacted. No source, test, migration, model, startup, Docker, or production configuration was modified.

## Result

```text
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE
BACKUP_RESTORE_VERIFICATION = UNAVAILABLE
MIGRATION_REPAIR = BLOCKED
```

The attachment provided for this run contains instructions only. It does not provide a PostgreSQL target, schema dump, baseline snapshot, provisioning artifact, or backup.

## Environment and identity

| Evidence | Finding |
|---|---|
| PostgreSQL version | Not verifiable. `docker`, `psql`, `pg_isready`, `postgres`, and `pg_ctl` are not available in the local environment. No local listener was found on port 5432. |
| Environment identity/type | No PostgreSQL database or target was provided; production/staging/development identity is unknown. No database was contacted. |
| Baseline date/time | Unknown; no authoritative artifact exists in the supplied material or repository. |
| Configured connection | No `DATABASE*`, `POSTGRES*`, `PGHOST`, `PGPORT`, `REDIS*`, or Alembic-related environment variable names are present in the current process environment. Compose files use variable-based templates; their values were not read or exposed. |
| Extensions and schemas | Unknown; requires inspection of an authoritative PostgreSQL instance or schema artifact. |
| Backup artifacts / restore procedure | No PostgreSQL dump or backup artifact was found. Repository disaster-recovery documentation says backup and restore are provided externally and no repository-specific automated procedure exists. |
| Repository database file | `data_quality.db` is tracked SQLite. It is not evidence of PostgreSQL production schema and was not used as a substitute. |

The repository's Compose files declare PostgreSQL 16 and Redis 7 images. This establishes intended deployment configuration only; Docker is unavailable here, so these services are not running or verifiable.

## Alembic evidence

- Static `alembic heads` reports one repository head: **`20260928_01`**.
- The migration chain contains one connected history from `0001_persistence` through `20260928_01`; the repository history has 23 revision files.
- The live database Alembic revision is **UNKNOWN**. `alembic current` was not run because it could attempt to connect to an unspecified database.
- Existing repository forensics found the first `datasets` reference at `d14c1f2a9b31` and no earlier migration creating `datasets`. The chain therefore does not establish an empty-database bootstrap. Prior evidence is consistent with a pre-provisioned starting schema, but does not identify the authoritative production baseline.
- No PostgreSQL schema was available to compare with Alembic history or SQLAlchemy metadata.

### Repository-declared table names (not a production inventory)

`database.models` declares ORM tables named: `organizations`, `organization_quotas`, `roles`, `compliance_policies`, `permissions`, `role_permissions`, `memberships`, `users`, `workspaces`, `channels`, `projects`, `datasets`, `sync_jobs`, `sync_attempts`, `workflows`, `workflow_versions`, `workflow_executions`, `executions`, `agent_memory`, `validation_logs`, `execution_traces`, `capability_execution_traces`, `approvals`, `risk_assessments`, `changesets`, `changeset_items`, `data_lineage_events`, `audit_events`, `risk_policies`, `reports`, and `channel_mappings`.

This is application-model evidence only. It does not establish which tables, columns, indexes, constraints, foreign keys, enums, extensions, or seed/reference rows exist in production.

## Schema comparison and migration findings

| Comparison item | Status |
|---|---|
| PostgreSQL baseline vs Alembic chain | **NOT PERFORMED — no authoritative PostgreSQL baseline** |
| PostgreSQL baseline vs ORM models | **NOT PERFORMED — no authoritative PostgreSQL baseline** |
| Critical tables, columns, indexes, constraints, foreign keys | **UNKNOWN** |
| PostgreSQL enum/types and extensions | **UNKNOWN** |
| Alembic upgrade from authoritative baseline | **UNKNOWN** |
| Empty PostgreSQL database bootstrap | **UNKNOWN in PostgreSQL**; repository chain has a known `datasets` starting-schema assumption and has not been proven from empty. |
| Current production/staging Alembic revision | **UNKNOWN** |
| Provisioning method / baseline revision | **UNKNOWN** |
| Backup/restore and rollback safety | **UNVERIFIED** |

No claim of PostgreSQL schema correctness, Alembic takeover safety, or production migration safety can be made from the available evidence.

## Commands and checks performed

- Checked availability of `docker`, `psql`, `pg_isready`, `postgres`, `pg_ctl`, `redis-cli`, and `redis-server`: all not found.
- Checked local listeners on PostgreSQL port 5432 and Redis port 6379: none found.
- Checked relevant environment variable **names only**: none present.
- Searched repository files for SQL dumps and backup/database artifacts: only tracked `data_quality.db` SQLite and local SQLite/cache files appeared; no PostgreSQL dump/backup was found.
- Ran `.\venv\Scripts\python.exe -m alembic heads`: `20260928_01 (head)`.
- Did not run `alembic current`, connect to any database, create a database, run application operations, or perform backup/restore.

## Required evidence to continue

Provide one authoritative PostgreSQL 16 baseline source:

1. schema-only dump from the authoritative environment; or
2. isolated PostgreSQL 16 staging database representing that baseline; or
3. authoritative provisioning artifact that creates the baseline schema.

Include metadata identifying environment type, PostgreSQL version, baseline date/revision, provisioning method, extensions, and current Alembic state. No credentials or application row data are required. Once supplied, verification must take place only in an isolated disposable PostgreSQL 16 environment, with explicit approval of its target before any connection. The baseline-to-head upgrade, fresh provisioning, API/worker startup, representative operations, schema differences, and backup/restore must then be tested without modifying the authoritative source.
