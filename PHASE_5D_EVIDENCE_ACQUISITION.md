# Phase 5D — PostgreSQL Baseline Evidence Acquisition & Re-entry Gate

**Date:** 2026-10-02  
**Purpose:** define the exact external evidence request and validation path. This is not a migration, database comparison, or production approval.

## 1. Current blocker

The repository documents PostgreSQL 16 as the intended production engine, but no authoritative production-equivalent PostgreSQL schema artifact, identified staging target, actual production Alembic revision, or backup/restore evidence is available. Consequently, the production baseline cannot be compared with the repository migration history. Phase 5C remains blocked; repair and production migration remain unauthorized.

## 2. Evidence already established

| Finding | Classification | Source / limit |
|---|---|---|
| PostgreSQL 16 and Redis 7 are the intended production runtime. | **DOCUMENTED** | `docs/production-deployment.md` and production Compose declare the versions. This is not proof of the deployed versions. |
| Production Compose defines a PostgreSQL service, persistent volume, and health check. | **DOCUMENTED** | `docker-compose.prod.yml`; a persistent volume is not a backup. |
| The repository Alembic head is documented as `20260928_01`; the runbook instructs operators to inspect current/head and apply `alembic upgrade head` through the deployment environment. | **DOCUMENTED** | `docs/operator/database-migration.md`; it does not establish any production database's current revision. |
| README describes the legacy schema auto-create path as local/test compatibility. | **DOCUMENTED** | `README.md`; not evidence of production provisioning history. |
| Production deployment instructions show Compose config/build/up and health verification but no explicit migration stage or complete provision → backup → migration → service startup sequence. | **DOCUMENTED** | `docs/production-deployment.md` and Compose files. |
| Disaster-recovery guidance says repository-specific automated backup/restore and `pg_dump`/`pg_restore` procedures are absent and backups are external. | **DOCUMENTED** | `docs/operator/disaster-recovery.md`. |
| CI workflow has no PostgreSQL service/database migration job. | **OBSERVED LOCALLY** | `.github/workflows/ci.yml` has no PostgreSQL service declaration; this says nothing about external CI/deployment systems. |
| A disposable PostgreSQL 16.15 verification container was inspected in Phase 5A; its database was empty with no application tables and no Alembic revision table. | **OBSERVED LOCALLY** | This is explicitly not production-equivalent evidence and is excluded from baseline inference. |
| A tracked SQLite `data_quality.db` exists in the repository. | **OBSERVED LOCALLY** | It is not PostgreSQL production evidence and is not used as a substitute. |
| An authoritative PostgreSQL schema-only dump, approved equivalent staging database, or authoritative schema provisioning artifact is available. | **UNKNOWN / not found** | None was supplied or identified in Phases 5B/5C. |
| Actual production schema, Alembic revision, provisioning history, deployment backup, and restore results. | **UNKNOWN** | No authoritative external artifact or report has been provided. |
| **AUTHORITATIVE EXTERNAL EVIDENCE** | **NONE PROVIDED** | No provenance-bearing production/staging schema artifact is currently available. |

Repository documentation is evidence of documented intent/procedure only. It is not evidence that an operation happened or that the production database matches it.

## 3. Evidence missing

Required before an authoritative schema comparison:

- PostgreSQL 16 schema-only baseline from production or explicitly approved production-equivalent staging.
- Provenance establishing environment identity, production/staging designation, source owner, capture time, and whether the artifact represents current state and was taken before/after a deployment.
- Source PostgreSQL version, database/schema/search path, required extensions, Alembic revision, and provisioning method, including whether historical application `create_all()` was used.
- Object definitions sufficient to inventory tables, columns/types, nullability/defaults, primary/foreign/unique constraints, indexes, sequences, enums/types, and relevant views.
- Role/ownership/grant information where it affects application behavior; if excluded, an authoritative statement of that omission and separate evidence for required grants.

Separately required before repair authorization:

- Actual production migration history and all supported starting states.
- Production backup provenance and a restore rehearsal into a separate disposable PostgreSQL 16 database.
- Evidence that restored schema/revision and representative reads/writes are valid.
- Production-to-head upgrade rehearsal and fresh-install provisioning proof.
- Data preservation, rollback/recovery, deployment ordering, and operator authorization.

## 4. Preferred artifact

### `POSTGRESQL_SCHEMA_ONLY_DUMP`

Request a schema-only PostgreSQL dump (for example, exported with `pg_dump --schema-only`) from the authoritative production database or explicitly approved production-equivalent PostgreSQL 16 staging environment.

The dump must include enough DDL to inspect application schemas and objects. It should contain no application row data. Request role/grant information if relevant; no passwords, connection strings, credentials, or secrets are required. Preserve the original artifact unchanged and provide a cryptographic checksum through the approved transfer channel.

## 5. Accepted alternatives

1. An explicitly approved isolated PostgreSQL 16 staging database with written confirmation that its schema and Alembic state represent production.
2. An authoritative schema snapshot exported from infrastructure/provisioning tooling, with equivalent provenance and revision metadata.
3. Another database baseline artifact only if its source owner explicitly approves it as representative of the production baseline and it exposes sufficient schema metadata.

An alternative can satisfy the baseline gate only when its source, equivalence, freshness, and limitations are documented. A staging label alone does not establish equivalence.

## 6. Rejected evidence types

The following do not establish a production baseline on their own:

- SQLite `data_quality.db` or other SQLite artifacts;
- `Base.metadata`, ORM model declarations, or `create_all()`;
- migration source/history by itself;
- Docker Compose image/service declarations;
- the empty Phase 5A disposable PostgreSQL database;
- an unidentified developer database or a database with unknown provenance;
- an assumed/guessed Alembic revision;
- screenshots without a provenance-bearing source artifact;
- an undocumented schema dump or a dump without environment identity and date.

## 7. Required provenance

The artifact submitter must provide each field below. If a critical field is absent or unverified, mark provenance **INCOMPLETE**; do not infer it.

```text
Environment:
Database:
Schema / search_path:
PostgreSQL version (major.minor):
Artifact creation timestamp and timezone:
Current Alembic revision (or authoritative explanation why unavailable):
Provisioning method:
Source owner / responsible operator:
Production or approved staging designation:
Evidence that staging is production-equivalent, if applicable:
Required extensions and versions:
Relevant roles / ownership / grants included or separately evidenced:
Schema-only confirmed (yes/no):
Artifact captured before/after which deployment:
Does artifact represent current environment state (yes/no/unknown):
Artifact checksum:
Known exclusions or limitations:
Historical application create_all() use (known / not used / unknown, with evidence):
```

No credentials or application row data should accompany the request.

## 8. Artifact validation procedure

Once provided, and before any database comparison:

1. Record receipt source, responsible owner, timestamp, checksum, and custody. Keep an unchanged original copy; perform inspection on a separate copy or read-only stream.
2. Validate the supplied PostgreSQL version is 16.x and the source is production or explicitly approved/equivalent staging.
3. Confirm the artifact is actually schema-only and does not contain application rows or secrets. If the artifact format is an archive, inspect its manifest without restoring it.
4. Confirm it contains identifiable schema definitions and adequate objects for tables, columns/types, nullability/defaults, keys/constraints, indexes, sequences, enums/types, extensions, and relevant views.
5. Independently establish the Alembic revision from provenance-bearing evidence. If unavailable, record `PRODUCTION_ALEMBIC_REVISION=UNKNOWN`; do not stamp or infer it from schema similarity.
6. Validate all provenance fields. Any unknown critical provenance keeps the artifact `INCOMPLETE`.
7. Only after validation, compare the artifact with ORM metadata, Alembic revisions/history, deployment configuration, and runbooks. Record object-by-object differences and confidence, and distinguish observed facts from interpretation.
8. Do not edit or normalize the submitted artifact. Any PostgreSQL restoration or migration experiment requires a separately authorized disposable target and a later explicit test plan.

## 9. Phase 5C re-entry criteria

Set `PHASE_5C_REENTRY=READY` only when **all** are true:

- authoritative PostgreSQL 16 schema evidence exists;
- provenance is sufficient and the source is production or explicitly approved production-equivalent staging;
- equivalence and freshness are explicit;
- Alembic revision is known, or authoritative evidence explains why it cannot be known;
- schema inventory is available at the required object detail;
- the artifact is verified schema-only and has not been substituted with ORM, SQLite, `create_all()`, migration source, or an empty database; and
- it can be compared with the repository Alembic history and expected objects.

Otherwise set `PHASE_5C_REENTRY=BLOCKED`. Re-entry only authorizes the Phase 5C evidence comparison; it does **not** authorize repair or production migration.

## 10. Repair gate

Even after the Phase 5C comparison is complete, keep `REPAIR_AUTHORIZATION=NOT_AUTHORIZED` until all of the following are evidenced and reviewed:

- production baseline and actual migration history are understood;
- schema/migration discrepancies and supported starting states are documented;
- fresh PostgreSQL 16 provisioning and upgrade from the actual production baseline are understood;
- destructive and data-transforming revisions are inventoried;
- backup/restore procedure and restore validation are evidenced;
- repair strategy is selected based on baseline evidence, not convenience;
- representative existing-state and fresh-install tests are planned and pass on disposable PostgreSQL 16 databases;
- rollback/downgrade and forward recovery implications are documented; and
- explicit authorization for repair is granted in a later phase.

## 11. Production migration gate

No production migration is authorized by Phase 5D. Before any future production migration require:

- authoritative production backup and its provenance;
- successful restore into a disposable PostgreSQL 16 database;
- schema and Alembic revision validation after restore;
- migration rehearsal against the restored representative state;
- representative application, API, and worker operations;
- row, constraint, index, and integrity checks appropriate to affected data;
- operational rollback/recovery plan and monitored recovery point;
- explicit deployment ordering, including database provisioning, backup, migration, API and worker startup;
- independent verification of the production Alembic revision; and
- explicit production authorization by the responsible operator.

## 12. Operator request checklist

### Request and provenance

- [ ] Obtain a PostgreSQL 16 schema-only dump from production or explicitly approved production-equivalent staging.
- [ ] Confirm environment identity and production/staging designation.
- [ ] Confirm staging equivalence to production, if applicable.
- [ ] Record PostgreSQL major/minor version.
- [ ] Record database/schema/search path and dump timestamp/timezone.
- [ ] Record current Alembic revision, or provide authoritative explanation if unavailable.
- [ ] Record provisioning method, including historical `create_all()` use if known.
- [ ] Record required extensions and versions.
- [ ] State whether relevant roles/grants are included or provide separate evidence.
- [ ] Confirm dump is schema-only and represents current state; identify deployment timing.
- [ ] Provide source owner, known exclusions, and artifact checksum.
- [ ] Preserve the original artifact unchanged for validation.
- [ ] Do **not** provide credentials, secrets, or application row data.

### Final state

```text
PHASE_5D=COMPLETE
PHASE_5C_REENTRY=BLOCKED
PRODUCTION_SCHEMA_BASELINE=UNKNOWN
PRODUCTION_ALEMBIC_REVISION=UNKNOWN
REPAIR_AUTHORIZATION=NOT_AUTHORIZED
PRODUCTION_MIGRATION_AUTHORIZATION=NOT_AUTHORIZED
NEXT_ACTION=OBTAIN_AUTHORITATIVE_POSTGRESQL_16_BASELINE
```
