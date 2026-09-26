# Rollback

## Application rollback

Production images are built from the repository Dockerfile and can be released using semantic version tags.

Before rollback, identify the deployed application image/version and the corresponding database migration state.

## ChangeSet rollback

The API exposes ChangeSet inspection and rollback operations.

Where a ChangeSet has an available rollback operation, use the ChangeSet rollback path rather than applying an unrelated direct mutation.

Production mutation remains subject to the platform's ChangeSet, risk and approval boundaries.

## Deployment rollback sequence

1. Stop promotion of the problematic application version.
2. Identify the last known application image/version.
3. Check the current database migration head.
4. Determine whether the application rollback is compatible with the current schema.
5. Restore the previous application version through the deployment system.
6. Verify `/healthz`.
7. Verify workflow worker connectivity.
8. Verify relevant application behavior and metrics.

## Database rollback

Database downgrade is a separate migration operation and must not be assumed to be required for every application rollback.

The repository currently tracks Alembic migration head `20260923_01`.

Do not downgrade a production database merely because an application image was rolled back. First establish schema compatibility and the migration dependency of the target application version.

## Verification

Record the rollback event and retain the deployment/version information needed for subsequent diagnosis.
