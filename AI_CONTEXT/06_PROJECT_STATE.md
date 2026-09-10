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
- S12 RAG / Semantic Rule Intelligence
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** `428 / 428 passing` (100% green via `python -m pytest -q`)
- **S12 Focused Tests:** `31 / 31 passing`
- **Semantic Agent Tests:** `7 / 7 passing`
- **Full Suite Execution Time:** ~21.7 seconds

## Database State

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Alembic Head Revision:** `b05fd7d45c87` (`b05fd7d45c87_enforce_workspace_ownership.py`)
- **Previous Migrations:**
  - `0001_persistence.py`
  - `7757af5afe0a_add_workspace_ownership.py`
- **S12 Migration:** None required. Semantic rule indexing is persisted separately in the Chroma vector store.

## Current Architecture

- **Pattern:** Clean Architecture + Domain-Driven Design (DDD).
- **Layers:**
  - `domain/`: Pure domain logic, entities, value objects, capability contracts, and semantic rule-retrieval contracts.
  - `application/`: Application services and use-case orchestration, including `RuleIntelligenceService`.
  - `execution/`: Runtime orchestration & engine (`execution/workflow`, `execution/capabilities`, `execution/context`, `execution/planning`, `execution/tracing`).
  - `infrastructure/`: Technical adapters including Chroma semantic rule retrieval.
  - `api/` & `app/`: Presentation layer (FastAPI routers, Streamlit dashboard, API client).
- **Composition Root:** `services/container.py`

## S12 Implementation

- Added domain `RuleRetriever` protocol with `RuleQuery`, `RetrievedRuleMatch`, and `SemanticRulePack`.
- Added persistent Chroma-backed `ChromaRuleRetriever` using `paraphrase-multilingual-MiniLM-L12-v2`.
- Added `RuleIntelligenceService` for semantic search, recommendation filtering, and explicit index synchronization.
- Extended `RuleRepository` / `RuleLoader` with `all()` for complete rule-set synchronization while preserving YAML parsing/versioning as the source of truth.
- Extended `RuleRetrieverAgent` with semantic `search()` while preserving the legacy deterministic `retrieve(category)` contract.
- Added FastAPI `/rules/search` and `/rules/recommend` endpoints.
- Added request/response schemas and dependency/container wiring.
- Added `chroma/` to `.gitignore`.
- Semantic indexing distinguishes descriptive rules from executable validation rules. Descriptive rules are never automatically treated as executable.
- Chroma synchronization is explicit; application startup does not automatically build or synchronize the semantic index.

## Current Focus

- S12 implementation is complete and fully tested.
- Next sprint: S13 Memory, subject to the roadmap and sprint specification.

## Known Constraints

- Do not rewrite existing architecture.
- Preserve backward-compatible APIs (`/validations`, `/executions`, etc.).
- Domain layer must remain strictly framework-independent.
- RAG/vector store implementation must remain isolated behind an infrastructure boundary.
- Retrieved semantic rules must not directly execute code.
- Executable validation continues to use registered declarative rule primitives.
- YAML rule definitions remain the source of truth for rule parsing and versioning.

## Known Risks

- Semantic retrieval quality depends on the embedding model and indexed rule corpus.
- The Chroma index must be explicitly synchronized when the YAML rule source changes.
- Future autonomous agent actions must adhere to ChangeSet and approval gates.
- Channel synchronization will require a canonical product schema.

## Next Action

- Begin S13 Memory according to `SPRINTS/sprint-13-memory.md`.
