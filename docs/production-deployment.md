# Production Deployment

## Required runtime

S26 production deployment uses:

- PostgreSQL 16
- Redis 7
- API container
- Redis-backed workflow workers
- Streamlit dashboard
- Nginx reverse proxy

The production Compose file does not publish API or dashboard ports directly.
Nginx is the public entrypoint on port 80.

## Configuration and secrets

Use `.env.production.example` as the variable template.

Real production values must be injected by the deployment environment, for example:

- a protected CI/CD environment;
- a cloud/container secret manager;
- an orchestrator secret store;
- an untracked deployment `.env` file with restricted filesystem permissions.

Do not commit:

- `POSTGRES_PASSWORD`;
- API keys;
- channel credentials;
- encryption keys;
- generated `.env` files containing real values.

`POSTGRES_PASSWORD` is required by `docker-compose.prod.yml`; there is no production fallback password.

## Production startup

After Docker is installed and configured:

docker compose --env-file .env.production -f docker-compose.prod.yml config
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

Verify the public health endpoint:

curl http://localhost/healthz

Expected response:

{"status":"ok"}

## Release images

Releases are created by pushing a semantic-version Git tag such as `v1.2.3`.

The release workflow:

1. builds the production Docker image;
2. publishes it to GitHub Container Registry;
3. creates semver image tags;
4. scans the image with Trivy;
5. fails the release job on HIGH or CRITICAL unfixed vulnerabilities.

## Deployment verification

A production deployment is considered verified only after:

1. Compose configuration succeeds with injected secrets;
2. production images build successfully;
3. all required services become healthy;
4. `/healthz` responds successfully through Nginx;
5. workflow execution can use the Redis-backed worker pool;
6. application metrics remain available through the API.
