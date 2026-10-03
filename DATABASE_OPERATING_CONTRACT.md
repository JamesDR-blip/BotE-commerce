# Database Operating Contract

## Selected migration model

`DATABASE_MIGRATION_MODEL = DEDICATED_MIGRATION_JOB`

Target database is PostgreSQL 16. This is first-production provisioning: no production/staging database or historical production baseline exists, and no production data requires preservation.

Production order: `PostgreSQL → Alembic migration job → schema validated → application/API → workers`. The migration job is the only production process authorized to change schema. API and worker startup must not run Alembic or `create_all()`. The production container's current revision check remains a startup guard, not a migration mechanism.

Local/development environments may run Alembic explicitly. ORM `create_all()` is not an alternative production bootstrap or a way to stamp/reconcile Alembic state. Schema migrations do not create demo/sample data. System RBAC reference seed is a separate idempotent step described in [`SYSTEM_SEED_CONTRACT.md`](SYSTEM_SEED_CONTRACT.md).

## Evidence and current gap

Repository evidence: `services/container.py` sets `create_schema=False` and requires current Alembic revision in production; API and worker share the container. `database/migrations/env.py` uses `Base.metadata`. `docs/operator/database-migration.md` documents the explicit migration-job path. Compose currently declares no migration job. The former active history's missing creators, duplicate/conflicting workspace changes, and `DATETIME` failure are addressed structurally by baseline `20261002_01`; PostgreSQL 16 execution and schema fingerprint remain unverified.

Therefore this remains the selected operating contract, not a validated deployment path. No Alembic command, application startup, database connection, or Docker operation was run during implementation.

## Required job contract before implementation

- Run exactly one approved migration job for a deployment release; serialize concurrent deployment attempts.
- Use a dedicated database identity with only the DDL privileges required for approved revisions; application/API/worker identities must not have schema-migration privileges. Exact role/grant SQL and credential delivery are not yet in repository evidence.
- Fail deployment if upgrade fails or schema validation/revision check fails; do not start API/workers on an unvalidated schema.
- Validate expected single Alembic head, revision, required objects/constraints/indexes, and supported system-reference seed state before traffic.
- Keep backup/restore and downgrade behavior explicit per release. No backup cadence, recovery-point objective, restore runbook, or production operation exists; no production baseline is being preserved.
- Rollback of application release does not imply automatic schema downgrade. Downgrade/forward-fix selection requires a reviewed compatibility plan.

## Remaining operational detail

Deployment platform, job definition, lock/serialization mechanism, dedicated role/grants, secret injection, backup policy, restore rehearsal, and schema-validation artifact are not implemented or evidenced. Resolve these before production deployment. The migration model is selected and the clean-install graph is implemented, but isolated PostgreSQL 16 validation remains a separate authorization and evidence gate.

```text
DATABASE_MIGRATION_MODEL = DEDICATED_MIGRATION_JOB
AUTOMATIC_STARTUP_MIGRATIONS = NO
APPLICATION_CREATE_ALL_IN_PRODUCTION = NO
MIGRATION_IMPLEMENTATION = IMPLEMENTED_STATICALLY
POSTGRESQL_16_VALIDATION = NOT_AUTHORIZED
```
