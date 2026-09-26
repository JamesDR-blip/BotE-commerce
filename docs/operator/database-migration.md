# Database Migration Runbook

## Current migration state

The repository uses Alembic with migrations under `database/migrations`.

The current repository head is `20260923_01`.

## Pre-migration checks

1. Confirm the target application version.
2. Confirm the configured production `DATABASE_URL`.
3. Confirm database availability.
4. Confirm a valid database backup exists through the deployment environment.
5. Review the migration chain before applying it.

## Inspect migration state

Standard Alembic inspection commands are `alembic current` and `alembic heads`.

## Apply migrations

Use the repository's Alembic configuration and apply migrations through the deployment environment with `alembic upgrade head`.

Do not manually edit the database to emulate an Alembic revision.

## Rollback

Downgrade is an explicit migration operation and should only be performed after verifying that the target application version is compatible with the downgraded schema.

Use the target Alembic revision identifier with `alembic downgrade REVISION`.

The repository documentation does not define a production-specific automated downgrade policy beyond the Alembic migration mechanism.

## Post-migration verification

After migration:
1. Check `alembic current`.
2. Start or restart application services as required.
3. Verify `/healthz`.
4. Verify worker connectivity.
5. Run the relevant application test suite or smoke checks.
6. Verify application metrics and audit behavior.

## Current head reference

The current head is `20260923_01`. S27 documentation does not add a database migration.
