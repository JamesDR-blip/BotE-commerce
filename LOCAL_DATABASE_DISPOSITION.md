# Local Database Disposition

**Owner policy:** `LOCAL_STATE = PRESERVE_UNTIL_INSPECTED`. Do not delete/reset tracked SQLite databases or persistent Compose volumes before classifying their contents and owner use. The owner identifies `aeop-postgres16-verify` as disposable PostgreSQL 16 verification infrastructure that must remain available. This document does not claim current runtime contents: no local DB or volume was inspected in this phase.

| Artifact/state | Evidence | Disposition | Allowed next action | Prohibited until classified/authorized |
|---|---|---|---|---|
| Tracked `data_quality.db` | Tracked SQLite file; root configuration points to SQLite; prior schema/revision evidence is historical and was not rechecked. | PRESERVE_UNTIL_INSPECTED | Read-only file metadata/inventory when authorized; make a safe copy only under an explicit preservation procedure. | Delete, reset, run `create_all()`, Alembic, or use as canonical PostgreSQL baseline. |
| Local `.env` database setting | User-specific SQLite URL configuration; value intentionally not reproduced. | PRESERVE | Inspect scheme/path without exposing credentials if an authorized configuration review is needed. | Rewrite environment settings or assume the pointed database is disposable. |
| Compose persistent PostgreSQL volume `postgres_data` | Compose declares a named persistent volume; actual existence/content/revision are unknown. | PRESERVE_UNTIL_INSPECTED | Inventory container/volume metadata read-only under separate authorization. | `down -v`, prune, recreate, migrate, or reset before classification. |
| `aeop-postgres16-verify` | Owner-designated disposable PostgreSQL 16 validation infrastructure. | KEEP AVAILABLE; disposable for explicitly authorized verification only | Use as isolated validation target only after its state/ownership is rechecked and the verification step is authorized. | Delete it, repurpose it as local app state or production baseline, or run Alembic without authorization. |
| Per-test temporary SQLite files | Test-scoped `tmp_path` state. | DISPOSABLE after the owning test run ends | Normal test cleanup. | Treat similarly named repository-root directories as pytest temp files without evidence. |
| In-memory SQLite engines | Process-scoped test state. | DISPOSABLE when process ends | Normal process teardown. | Use as PostgreSQL behavior evidence. |
| Compose/deployment templates and `.env.example` files | Configuration, not database state. | PRESERVE | Read as configuration evidence. | Treat as proof of a live production/staging database. |

## Classification needed before any local transition

For each persistent SQLite file or PostgreSQL volume, record location/owner, engine/version, whether it contains user/development/sample data, current schema fingerprint, any Alembic revision (if present), backup copy location, and explicit keep/recreate/migrate decision. Do not inspect by connecting until separately authorized. Owner confirms there is no production/staging data to preserve; that does not classify developer-local data.

```text
LOCAL_STATE = PRESERVE_UNTIL_INSPECTED
PRODUCTION_OR_STAGING_BASELINE = NONE
LOCAL_PERSISTENT_CONTENTS = UNINSPECTED
VERIFICATION_CONTAINER = KEEP_AVAILABLE
DESTRUCTIVE_ACTIONS = NOT_AUTHORIZED
```
