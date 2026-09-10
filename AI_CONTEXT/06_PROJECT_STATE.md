# PROJECT STATE

## Current Sprint

**S13 - Agent Memory & Execution Context**

## Previous Sprints

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
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** `446 / 446 passing` (100% green via `python -m pytest -q`)
- **S13 Integration Acceptance:** `2 / 2 passing`
- **S13 Repository Tests:** `5 / 5 passing`
- **S13 Service Tests:** `6 / 6 passing`
- **S13 Parameter / Requirement Tests:** `21 / 21 passing`
- **Full Suite Execution Time:** ~23.9 seconds
- **Warnings:** 1 dependency deprecation warning from Starlette/AnyIO TestClient.

## Database State

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Alembic Head Revision:** `c13a7e91d204` (`add_agent_memory`)
- **Previous Head:** `b05fd7d45c87` (`b05fd7d45c87_enforce_workspace_ownership.py`)
- **S13 Migration:** Added tenant-scoped persistent `agent_memory` storage.
- **Memory Storage:** SQLAlchemy `AgentMemoryRecord` persisted in `agent_memory`.
- **Memory Scope:** Strictly scoped by `workspace_id` and `user_id`.
- **Expiration:** Optional `expires_at` with query-time filtering and explicit eviction.

## Current Architecture

- **Pattern:** Clean Architecture + Domain-Driven Design (DDD).
- **Layers:**
  - `domain/`: Pure domain logic, entities, value objects, capability contracts, and semantic rule-retrieval contracts.
  - `application/`: Application services and use-case orchestration, including rule intelligence and agent memory services.
  - `execution/`: Runtime orchestration & engine (`execution/workflow`, `execution/capabilities`, `execution/context`, `execution/planning`, `execution/tracing`).
  - `infrastructure/`: Technical adapters including Chroma semantic rule retrieval.
  - `api/` & `app/`: Presentation layer (FastAPI routers, Streamlit dashboard, API client).
- **Composition Root:** `services/container.py`

## S13 Implementation

- Added domain `AgentMemory`, `CorrectionEvent`, and `ExecutionLearning` models.
- Added tenant-scoped `AgentMemoryRecord` persistence model.
- Added `AgentMemoryRepository` with workspace/user isolation, expiration filtering, and expired-memory eviction.
- Added `AgentMemoryService` for recording corrections and execution learning.
- Added recursive PII redaction before memory persistence using an explicit sensitive-key allowlist.
- Extended `ParameterResolver` with optional tenant-scoped memory retrieval.
- Memory corrections are applied only after validation against the requested capability's declared parameter contract.
- Extended `RequirementInterpreter` and `RequirementAgent` to propagate optional tenant scope.
- Wired memory through `services/container.py`.
- Preserved deterministic parameter resolution and backward-compatible invocation when memory or tenant scope is unavailable.
- Added integration coverage proving persisted corrections affect subsequent requirement interpretation and proving workspace/user tenant isolation.

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

- S13 Memory implementation is complete and fully tested.
- Persisted agent memory is currently consumed by `ParameterResolver` through the `RequirementAgent` / `RequirementInterpreter` path.
- `QualityService` is intentionally not wired to memory because its current contract does not carry tenant scope.
- Next sprint: follow the roadmap after S13.

## Known Constraints

- Do not rewrite existing architecture.
- Preserve backward-compatible APIs (`/validations`, `/executions`, etc.).
- Domain layer must remain strictly framework-independent.
- RAG/vector store implementation must remain isolated behind an infrastructure boundary.
- Retrieved semantic rules must not directly execute code.
- Executable validation continues to use registered declarative rule primitives.
- YAML rule definitions remain the source of truth for rule parsing and versioning.
- Agent memory must remain strictly tenant-scoped by workspace and user.
- Persisted memory must not retain explicitly sensitive customer PII.
- Memory-derived parameters must be validated against declared capability contracts before application.

## Known Risks

- Semantic retrieval quality depends on the embedding model and indexed rule corpus.
- The Chroma index must be explicitly synchronized when the YAML rule source changes.
- Memory quality depends on the correctness and relevance of recorded corrections.
- Future memory retrieval strategies may require ranking, deduplication, TTL policies, or broader execution-learning integration.
- Future autonomous agent actions must adhere to ChangeSet and approval gates.
- Channel synchronization will require a canonical product schema.

## Next Action

- Proceed to the next roadmap sprint after S13 Memory, using the repository workflow and handoff documents as the source of truth.