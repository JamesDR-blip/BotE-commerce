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

The canonical baseline is intentionally not downgradeable; its `downgrade()` raises an explicit error. Database rollback therefore requires restoring a matching verified backup or using a separately reviewed forward fix. Do not assume a revision downgrade can reverse the baseline.

The active repository head is `20261002_01`. The former 23-revision history is preserved as an inactive archive under `database/migrations/archive/legacy_versions/`; those IDs are not active heads.

Do not downgrade a production database merely because an application image was rolled back. First establish schema compatibility and the migration dependency of the target application version.

## Verification

Record the rollback event and retain the deployment/version information needed for subsequent diagnosis.
