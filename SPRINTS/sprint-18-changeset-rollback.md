# SPRINT 18: ChangeSet & Atomic Rollback Engine

## Status
COMPLETE

## Implementation Completed

### Domain
- Added immutable `ChangeSet` aggregate.
- Added immutable `ChangeSetItem`.
- Added `ChangeSetStatus` lifecycle:
  - `PREPARED`
  - `APPLIED`
  - `ROLLED_BACK`

### Application
- Added `ChangeSetService` for candidate ChangeSet preparation.
- Added immutable after-artifact materialization with SHA-256 verification.
- Added `ChangeSetMutationService`.
- Added `ChangeSetRollbackService`.
- Added `ApprovalChangeSetService` for atomic approval-to-apply execution.

### Persistence
- Added `changesets` table.
- Added `changeset_items` table.
- Added `ChangeSetRepository`.
- Added approval → ChangeSet foreign key.
- Added optimistic-concurrency guards for Apply and Rollback.

### API
- Added `GET /changesets`.
- Added `GET /changesets/{changeset_id}`.
- Added `POST /changesets/{changeset_id}/rollback`.

### Runtime / Safety
- High-risk executions materialize a candidate ChangeSet before entering `PENDING_APPROVAL`.
- Approval applies the prepared ChangeSet atomically.
- Approved ChangeSet-backed executions do not return to the workflow queue.
- Rejected executions become `CANCELLED`.
- Production `DatasetRecord` mutation is restricted to the ChangeSet repository boundary.
- Rollback restores the immutable before-artifact pointer atomically.

## Verification

- Full regression: **591 passed**.
- Full suite runtime: **28.05 seconds**.
- `python -m compileall` passed for production Python packages.
- ChangeSet API tests passed.
- ChangeSet preparation, repository, mutation, rollback, artifact materialization, and approval integration tests passed.
- Alembic current/head: `20260914_02`.
- S18 migrations:
  - `20260914_01_add_changesets.py`
  - `20260914_02_add_approval_changeset_fk.py`
- One existing Starlette/AnyIO TestClient deprecation warning remains.
- `alembic check` reports seven pre-existing model/schema drift operations unrelated to S18.