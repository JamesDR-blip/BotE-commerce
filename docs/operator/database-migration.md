# Database Migration Runbook

## Current migration state

The repository uses Alembic with migrations under `database/migrations`.

The active repository head is `20261002_01` (canonical PostgreSQL baseline). The former 23-revision history is preserved in `database/migrations/archive/legacy_versions/` and is not an active lineage.

The baseline passed fresh-install validation on disposable PostgreSQL 16.15. The observed schema had 31 application tables, 43 foreign keys, 67 explicit/application indexes, and 109 total indexes; representative persistence Groups 1–7 passed. This local verification is not production-equivalent and does not establish production migration safety. The project has never been deployed to production or staging and has no production data to preserve. Production migration authorization remains unestablished while production schema/revision evidence, backup/restore evidence, production-equivalent upgrade rehearsal, and deployment/provisioning order remain unresolved.

Schema changes follow the dedicated migration-job model: PostgreSQL → Alembic migration job → schema validation → application/API → workers. Application/API and worker startup must not execute automatic Alembic migrations.

## Pre-migration checks

1. Confirm the target application version.
2. Confirm the configured production `DATABASE_URL`.
3. Confirm database availability.
4. Confirm a valid database backup exists through the deployment environment.
5. Review the migration chain before applying it.

## Inspect migration state

`alembic heads` inspects the repository graph without a database. `alembic current` connects to the configured database: use it only after confirming the database identity and authorization. Archived revision states are not recognized by the new active lineage; do not probe or migrate an existing local database before its state is classified and backed up.

## Apply migrations

For a newly provisioned, verified-empty PostgreSQL 16 database, the dedicated migration-job command is `alembic upgrade head`; this path was validated locally against the disposable PostgreSQL 16.15 database. That validation does not authorize production execution. Do not run this against SQLite, `create_all()`-initialized databases, or databases carrying one of the archived revision IDs unless a state-specific adoption procedure has been separately reviewed and authorized.

Do not manually edit the database to emulate an Alembic revision.

## Rollback

The canonical baseline is intentionally not downgradeable; its `downgrade()` raises an explicit error. Recovery requires restoring a matching verified database backup or using a separately reviewed forward fix. Do not run `alembic downgrade` as a rollback assumption.

## Post-migration verification

After migration:
1. Check `alembic current`.
2. Start or restart application services as required.
3. Verify `/healthz`.
4. Verify worker connectivity.
5. Run the relevant application test suite or smoke checks.
6. Verify application metrics and audit behavior.

## Current head reference

The active head is `20261002_01`. Update this reference when the active Alembic head advances; archived historical revision IDs are not current heads.
