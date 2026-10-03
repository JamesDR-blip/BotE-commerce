# Production Baseline Comparison — Evidence Gate

**Review date:** 2026-10-02  
**Result:** No authoritative production-equivalent PostgreSQL schema artifact or approved staging target was supplied or found. A schema comparison cannot be performed without fabricating baseline facts, so this report records the missing evidence only.

## Evidence available

- The supplied attachment contains Phase 5B instructions only; it does not include a schema dump or staging connection target.
- A narrow repository search found no PostgreSQL schema dump, backup, or provisioning artifact (`.sql`, `.dump`, `.bak`, `.backup`, `.schema`, or `.psql`).
- Phase 5A previously verified a separate disposable PostgreSQL **16.15** container and an empty `dataquality_verify` database. That database had no application tables and no `alembic_version` table. It is not production-equivalent evidence and is not used to infer production schema.
- No production connection was attempted in this phase. No database was modified.

## Comparison status

| Requested comparison | Status |
|---|---|
| Environment identity / production or approved staging | **UNKNOWN — artifact absent** |
| PostgreSQL major/minor version of authoritative baseline | **UNKNOWN**; disposable verification runtime separately observed as 16.15 |
| Dump timestamp and schema/database name | **UNKNOWN** |
| Provisioning method, including historical `create_all()` use | **UNKNOWN** |
| Production Alembic revision | **UNKNOWN** |
| Required extensions | **UNKNOWN** |
| Schema/table/column/type inventory | **NOT COMPARED** |
| Primary/foreign/unique constraints, indexes, defaults, nullability | **NOT COMPARED** |
| Enums/types, views, sequences | **NOT COMPARED** |
| Roles, ownership, and grants | **UNKNOWN / NOT COMPARED** |
| ORM-vs-production differences | **NOT COMPARED** |
| Alembic-vs-production differences and migration applicability | **NOT COMPARED** |
| Missing or extra objects | **UNKNOWN** |
| Production data preservation | **NOT DEMONSTRATED** |
| Backup/restore evidence | **UNAVAILABLE** |

The known repository migration issues from Phase 5A remain repository findings, not a comparison against production: the empty-database attempt failed at `7757af5afe0a` on raw `DATETIME`; the chain has a conflicting workspace lifecycle; and no migration creates `datasets` or several other ORM-declared tables. The production baseline and applied revision remain unknown.

## Minimum evidence required

Provide **one authoritative PostgreSQL 16 schema-only dump from production or explicitly approved production-equivalent staging**, with no application row data or secrets. Include:

- environment identity/type;
- PostgreSQL major/minor version;
- dump timestamp and schema/database name;
- provisioning method and whether application `create_all()` was used;
- current Alembic revision, if any;
- required extensions; and
- whether roles/grants are included.

An explicitly approved isolated staging PostgreSQL 16 database known to match production is an acceptable alternative if a dump cannot be provided. Do not connect to production absent that authoritative artifact/authorization.

## PHASE_5B_DECISION

```text
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
POSTGRESQL_VERSION = UNKNOWN
PRODUCTION_ALEMBIC_REVISION = UNKNOWN
SCHEMA_COMPARISON = INCOMPLETE
PROVISIONING_METHOD = UNKNOWN
BACKUP_RESTORE_EVIDENCE = UNAVAILABLE
REPAIR_AUTHORIZATION = NOT_AUTHORIZED
PHASE_5B = INCOMPLETE
NEXT_ACTION = Provide the authoritative PostgreSQL 16 schema-only dump with the required provenance and Alembic metadata listed above.
```

Phase 5 remains **NO-GO**. No source, test, Alembic, database, model, startup, deployment, or configuration file was changed. No migration, test suite, backup, or restore operation was run in this evidence gate.
