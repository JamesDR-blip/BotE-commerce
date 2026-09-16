# S21 Sprint Handoff

## Status

S21 — Channel Sync & Multi-Platform Connectors: COMPLETE.

S21 establishes the first external-channel synchronization layer while preserving the existing ChangeSet, approval, lineage, audit, and authorization boundaries.

## Completed Work

### Domain

- CanonicalProduct.
- ChannelMapping.
- Channel.
- SyncJob.
- SyncAttempt.
- Connector, ConnectorRequest and ConnectorResult.
- Explicit SyncJob state transitions.

### Application

- CanonicalProductService.
- ChannelSyncService.
- Deterministic product projection and hashing.
- Create/update/noop delta handling.
- Sync-job idempotency.
- SyncAttempt persistence.
- ChannelMapping reconciliation.
- Owner/workspace authorization.
- Sync lifecycle audit events.

### Infrastructure / Security

- Channel HTTP client with bounded retry/backoff.
- Connector factory.
- Shopify connector.
- Amazon SP-API connector.
- CredentialCipher abstraction.
- Fernet credential encryption.
- Fail-closed unavailable credential cipher.
- Channel/sync-job/attempt/mapping repositories.

### API

- `GET /channels`
- `POST /channels/{channel_id}/sync`
- `GET /sync-jobs/{sync_job_id}`

Credentials are never exposed through API responses.

## Architecture Decisions

1. Keep ChangeSet as the only internal production dataset mutation boundary.
2. Treat external channel API operations as an external side-effect boundary.
3. Reuse existing dataset, storage, mapping and normalization abstractions.
4. Keep channel contracts in Domain.
5. Keep synchronization orchestration in Application.
6. Keep HTTP/channel integrations in Infrastructure.
7. Inject credential encryption rather than storing plaintext credentials.
8. Fail closed when credential encryption is unavailable.
9. Enforce idempotency at both application and database levels.
10. Use deterministic product hashes for noop/delta decisions.
11. Implement Shopify and Amazon SP-API according to S21 verification scope.
12. Do not fabricate Amazon SigV4 signing; production-grade signing remains deferred.
13. Keep unsupported channels explicit rather than creating unsafe placeholders.

## Security / Safety

- Credentials encrypted at rest.
- Credentials excluded from API responses.
- Owner/workspace authorization enforced.
- No plaintext credential fallback.
- No unsafe eval/exec.
- No unsafe YAML loading.
- No arbitrary SQL.
- Bounded HTTP retry/backoff.

## Database / Migration

- `20260916_01_add_channels.py`
- `20260916_02_add_sync_jobs.py`
- `20260916_03_add_channel_mappings.py`

Current Alembic head: `20260916_03`.

Seven pre-existing model/schema drift operations remain outside S21 scope.

## Verification

- Full regression: **706 passed, 1 warning**.
- S21 targeted coverage: **57 passed**.
- S21 API coverage: **11 passed, 1 warning**.
- `python -m compileall`: PASS.
- `git diff --check`: PASS.
- Alembic current/head: `20260916_03`.

## Files Added

- `api/routes/channels.py`
- `application/channels/__init__.py`
- `application/channels/canonical_product_service.py`
- `application/channels/channel_sync_service.py`
- `application/channels/credential_cipher.py`
- `database/migrations/versions/20260916_01_add_channels.py`
- `database/migrations/versions/20260916_02_add_sync_jobs.py`
- `database/migrations/versions/20260916_03_add_channel_mappings.py`
- `domain/channel_sync.py`
- `infrastructure/channels/__init__.py`
- `infrastructure/channels/amazon_sp_api.py`
- `infrastructure/channels/factory.py`
- `infrastructure/channels/http_client.py`
- `infrastructure/channels/shopify.py`
- `infrastructure/security/credential_cipher.py`
- `infrastructure/security/unavailable_credential_cipher.py`
- `repositories/channel_mappings.py`
- `repositories/channels.py`
- `repositories/sync_jobs.py`
- `tests/test_api_channels.py`
- `tests/test_canonical_product_service.py`
- `tests/test_channel_connectors.py`
- `tests/test_channel_repository.py`
- `tests/test_channel_sync_domain.py`
- `tests/test_channel_sync_service.py`
- `tests/test_credential_cipher.py`
- `tests/test_sync_job_repository.py`

## Files Modified

- `api/dependencies.py`
- `api/main.py`
- `api/routes/__init__.py`
- `configs/settings.py`
- `database/models.py`
- `requirements.txt`
- `schemas/requests.py`
- `schemas/responses.py`
- `services/container.py`

`data_quality.db` is a tracked local database artifact advanced by the S21 migrations and should be handled according to repository database-artifact policy.

## Known Issues / Deferred Work

1. TikTok Shop connector remains unimplemented.
2. Shopee connector remains unimplemented.
3. Lazada connector remains unimplemented.
4. Amazon SP-API SigV4 production authentication/signing remains deferred.
5. Dedicated channel/distributed rate limiting remains deferred.
6. Durable asynchronous channel workers remain deferred.
7. Cross-product external compensation/reconciliation remains deferred.
8. Streaming ChangeSet preparation remains unsupported.
9. Seven pre-existing Alembic drift operations remain.
10. Existing Starlette/AnyIO deprecation warning remains.
11. S19 artifact-level lineage and audit retention enforcement remain deferred.

## Next Sprint

S22 — AI Copilot for Data Operations.

S22 should build on the existing governed application, ChangeSet, approval, lineage, audit, and channel-sync boundaries rather than introducing a parallel mutation or authorization path.
