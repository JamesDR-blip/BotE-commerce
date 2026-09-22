# PROJECT STATE

## Current Sprint

**S24 — Enterprise Governance & Granular RBAC: IN PROGRESS**


## Next Sprint

**S24 Enterprise Governance & Granular RBAC**

## Previous Sprints

- **S14** - Performance, Streaming & Asynchronous Workers
- **S13** - Agent Memory & Execution Context
- **S12** - RAG / Rule Intelligence
- **S11** - Streamlit Dashboard & HTTP Client
- **Clean Architecture Refactoring** - Reorganized packages into Domain, Application, Execution, and Infrastructure layers; added domain serialization and Cache protocol.

## Completed Milestones

- S00 Architecture Audit / Refactor
- S01 Project Structure & Conventions
- S02 Configuration / Logging
- S03 Plugin Architecture
- S04 Safe YAML Rule Engine
- S05 Capability Decomposition
- S06 LangGraph Orchestration
- S07 AI Collaborator Agents
- S08 Product Attribute Extraction
- S09 FastAPI Presentation Layer
- S10 Persistence & Alembic Migrations
- S11 Streamlit Dashboard
- S12 RAG / Semantic Rule Intelligence
- S13 Agent Memory & Execution Context
- S14 Performance
- S15 Data Health Command Center
- S16 Risk & Approval Engine
- S17 Shadow Mode & Simulation
- S18 ChangeSet & Rollback
- S19 Data Lineage & Audit Trail
- S20 Autonomous Agent Operations
- S21 Channel Sync & Multi-Platform Connectors
- S22 AI Copilot for Data Operations
- S23 Marketplace & Extensibility Ecosystem
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** 612 / 612 passing via python -m pytest
- **Latest Full Suite Runtime:** 26.65 seconds
- **Warnings:** 1 existing Starlette/AnyIO TestClient deprecation warning.
- S19 lineage, audit, API, ChangeSet, approval, rollback, repository, and workflow integration tests all pass.
- git diff --check: no whitespace errors; remaining messages are Git LF/CRLF normalization warnings.

## Database / Migration Status

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Current Database Revision:** 20260916_03
- **Current local database revision:** `20260916_03`.
- **Repository Alembic head:** `20260916_03`.
- **Latest migrations:** S21 channel synchronization migrations:
  - `database/migrations/versions/20260916_01_add_channels.py`
  - `database/migrations/versions/20260916_02_add_sync_jobs.py`
  - `database/migrations/versions/20260916_03_add_channel_mappings.py`
- **S22 database migration:** none required.
- Alembic currently reports a single head: `20260916_03`.
- Seven pre-existing model/schema drift operations remain outside S22 scope.
- Existing clean-from-zero Alembic baseline/bootstrap limitations remain outside S22 scope.

## Current Architecture

- **Pattern:** Clean Architecture + Domain-Driven Design (DDD).
- **Layers:**
  - `domain/`: Pure domain logic, entities, value objects, capability contracts, and semantic rule-retrieval contracts.
  - `application/`: Application services and use-case orchestration, including rule intelligence and agent memory services.
  - `execution/`: Runtime orchestration & engine (`execution/workflow`, `execution/capabilities`, `execution/context`, `execution/planning`, `execution/tracing`).
  - `infrastructure/`: Technical adapters including Chroma semantic rule retrieval.
  - `api/` & `app/`: Presentation layer (FastAPI routers, Streamlit dashboard, API client).
- **Composition Root:** `services/container.py`

## Current Sprint

S24 — Enterprise Governance & Granular RBAC: IN PROGRESS.

The verified S24 implementation currently covers persistent RBAC, organization membership, tenant-scoped repository access, and authorization enforcement across the existing workspace, dataset, workflow, and approval resources.

Organization quotas and compliance policy enforcement remain outstanding S24 scope.

## S24 Governance & RBAC

### Delivered

- Persistent organization model.
- Persistent role model.
- Persistent permission model.
- Role-permission assignments.
- User organization memberships.
- Admin, Data Engineer, Reviewer, and Viewer role definitions.
- `AuthorizationService` with persisted RBAC as the authoritative authorization source when configured.
- Backward-compatible legacy role authorization fallback.
- Organization-aware workspace access.
- Organization-aware project access through workspace tenancy.
- Organization-aware dataset access through project/workspace tenancy.
- Organization-aware workflow and workflow-version access.
- Organization-aware approval access.
- Organization-scoped pending approval queries.
- Authenticated `/approvals/pending` access.
- Workspace organization ownership relationship.
- Tenant filtering through repository boundaries.
- Authorization injection through the composition root.

### Architecture / Security

- Clean Architecture + DDD boundaries remain intact.
- Domain authorization contracts remain framework-independent.
- Application services orchestrate authorization; repositories enforce tenant-scoped persistence queries.
- Existing ownership boundaries remain authoritative.
- Organization scope does not replace resource ownership.
- ChangeSet remains the only internal production dataset mutation boundary.
- No arbitrary SQL, Python, shell, `eval`, or `exec` capability was introduced.
- No unvalidated LLM output is used as an authorization decision.
- Approval tokens remain protected and are not exposed by pending-approval API responses.

### Database

S24 adds:

- `organizations`
- `roles`
- `permissions`
- `role_permissions`
- `memberships`
- nullable `workspaces.organization_id` with foreign-key and index support.

Migration:

`database/migrations/versions/20260916_04_add_enterprise_rbac.py`

Current Alembic revision/head:

`20260916_04`

A single Alembic head is confirmed.

### Verification

- Full regression: **887 passed, 2 warnings**.
- Latest full-suite runtime: **56.86 seconds**.
- `git diff --check`: no whitespace errors; existing LF/CRLF normalization warnings remain.
- Alembic current/head: `20260916_04`.
- Single Alembic head confirmed.

### Known Boundaries

- Organization quotas are not yet implemented.
- Compliance policy enforcement is not yet implemented.
- Existing Starlette/AnyIO TestClient deprecation warning remains.
- Existing marketplace installer duplicate `rules/fashion.yaml` warning remains.
- Existing pre-S24 schema/model drift and bootstrap limitations remain outside S24 scope where applicable.