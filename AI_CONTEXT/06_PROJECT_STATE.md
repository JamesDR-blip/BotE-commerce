# PROJECT STATE

## Current Sprint

**S12 - RAG / Rule Intelligence**

## Previous Sprints

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
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** `396 / 396 passing` (100% green via `pytest tests`)
- **Execution Time:** ~4.4 seconds

## Database State

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Alembic Head Revision:** `b05fd7d45c87` (`b05fd7d45c87_enforce_workspace_ownership.py`)
- **Previous Migrations:**
  - `0001_persistence.py`
  - `7757af5afe0a_add_workspace_ownership.py`

## Current Architecture

- **Pattern:** Clean Architecture + Domain-Driven Design (DDD).
- **Layers:**
  - `domain/`: Pure domain logic, entities, value objects, capability contracts (`domain/studio`, `domain/catalog`, `domain/quality`, `domain/validation`, `domain/serialization`).
  - `application/`: Application services (`application/workspace`, `application/datasets`, `application/workflows`, `application/quality`, `application/cache.py`).
  - `execution/`: Runtime orchestration & engine (`execution/workflow`, `execution/capabilities`, `execution/context`, `execution/planning`, `execution/tracing`).
  - `infrastructure/`: Adapters & technical services (`infrastructure/cache`, `infrastructure/observability`, `infrastructure/persistence`, `infrastructure/upload`).
  - `api/` & `app/`: Presentation layer (FastAPI routers, Streamlit dashboard, API client).
- **Composition Root:** `services/container.py`

## Current Focus

- Sprint S12: Design and implement semantic rule retrieval (`RuleRetriever` abstraction, vector index boundary, rule pack query integration).

## Known Constraints

- Do not rewrite existing architecture.
- Preserve backward-compatible APIs (`/validations`, `/executions`, etc.).
- Domain layer must remain strictly framework-independent.
- RAG/vector store implementation must be isolated behind an infrastructure boundary.

## Known Risks

- Context drift between documentation and implementation (resolved in documentation sync).
- Future autonomous agent actions must adhere to ChangeSet and approval gates.
- Channel synchronization will require a canonical product schema.

## Next Action

- Design `RuleRetriever` port in `domain/` or `application/` and Chroma/vector store adapter in `infrastructure/`.
