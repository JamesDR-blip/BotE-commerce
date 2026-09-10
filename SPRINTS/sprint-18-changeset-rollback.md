# SPRINT 18: ChangeSet & Atomic Rollback Engine

## Status
Backlog

## Objective
Fulfill the fundamental Project Constitution principle: Every production mutation must be an immutable `ChangeSet` capable of atomic, reversible rollbacks.

## Architectural Layer Impact
- **Domain Layer (`domain/`):**
  - Define `ChangeSet` aggregate root and `ChangeSetItem` (entity, record_id, before_snapshot, after_snapshot).
  - Define `RollbackTransaction` domain model.
- **Application Layer (`application/`):**
  - Implement `ChangeSetService` generating changesets from pipeline outputs.
  - Implement `RollbackService` restoring prior state.
- **Database Layer (`database/` & `repositories/`):**
  - `changesets` and `changeset_items` tables with Alembic migration.
  - `ChangeSetRepository`.
- **API Layer (`api/routes/changesets.py`):**
  - `GET /changesets`, `GET /changesets/{id}`, `POST /changesets/{id}/rollback`.

## Security & Constraints
- ChangeSets are append-only and strictly immutable.
- Rollbacks must be transactional (all-or-nothing).

## Verification Criteria
- Test creating a ChangeSet from auto-fix operations.
- Test performing a rollback and verifying dataset returns to identical prior state.
