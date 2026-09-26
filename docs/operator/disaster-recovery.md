# Disaster Recovery

## Recovery scope

Production Compose currently uses PostgreSQL 16, Redis 7, API, Redis-backed workflow workers, Streamlit dashboard and Nginx.

Persistent Compose volumes include:

- `postgres_data`;
- `redis_data`;
- `artifacts`.

## Recovery priorities

1. Restore PostgreSQL data.
2. Restore required application artifacts.
3. Restore Redis according to the operational recovery policy.
4. Start API, workers and dashboard.
5. Verify Nginx health routing.
6. Verify workflow execution and application metrics.

## Repository-supported verification

The production deployment configuration defines health checks for PostgreSQL, Redis and API. Nginx exposes the API health endpoint through `/healthz`.

After recovery, verify:

`	ext
GET /healthz
workflow execution through the Redis worker pool
application metrics
`"
"


The repository does not currently provide a documented automated backup/restore implementation or repository-specific `pg_dump`/`pg_restore` procedure.

Do not treat the Compose volume definitions as a backup system.

Database and artifact backups must therefore be provided by the deployment environment or an external backup system until repository automation is introduced.

## Secrets

Production secrets must not be committed to the repository. Use protected CI/CD configuration, a cloud/container secret manager, an orchestrator secret store, or an appropriately restricted untracked production environment file.
