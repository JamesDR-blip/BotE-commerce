# PROJECT STATE

## Current Sprint

**S14 - Performance / Async Workflow Execution**

## Previous Sprints

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
- S14-A Async Workflow Execution
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** `484 / 484 passing` (100% green via `python -m pytest -q`)
- **S14-A Targeted Regression:** `32 / 32 passing`
- **Full Suite Execution Time:** ~25.9 seconds
- **Warnings:** 1 dependency deprecation warning from Starlette/AnyIO TestClient.
- **S13 Integration Acceptance:** `2 / 2 passing`
- **S13 Repository Tests:** `5 / 5 passing`
- **S13 Service Tests:** `6 / 6 passing`
- **S13 Parameter / Requirement Tests:** `21 / 21 passing`

## Database State

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Current Database Revision:** `c13a7e91d204` (`add_agent_memory`)
- **Repository Alembic Head:** `d14c1f2a9b31` (`add_dataset_storage_key`)
- **Migration State:** Database is one migration behind repository head; `d14c1f2a9b31` has not been applied to the current local database during S14-A verification.
- **S13 Migration:** Added tenant-scoped persistent `agent_memory` storage.
- **Memory Storage:** SQLAlchemy `AgentMemoryRecord` persisted in `agent_memory`.
- **Memory Scope:** Strictly scoped by `workspace_id` and `user_id`.
- **Expiration:** Optional `expires_at` with query-time filtering and explicit eviction.
- **S14-A Database Change:** No new database migration was required for async workflow execution; `QUEUED` uses the existing workflow execution status column.

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

## S14-A Implementation

- Added `QUEUED` to the workflow execution status model.
- Added an application-level `WorkflowExecutionQueue` port.
- Added an in-process infrastructure queue adapter using a background daemon worker thread.
- Added atomic `QUEUED -> RUNNING` execution claiming to prevent duplicate queue delivery from executing the same persisted execution concurrently.
- Extended `WorkflowEngine` with queued execution creation and persisted execution resumption while preserving the existing synchronous execution path.
- Added `WorkflowExecutionWorker` that receives only a persisted `execution_id`, claims the execution, reloads its persisted workflow version and inputs, and reuses the existing `WorkflowEngine` runtime.
- Added `WorkflowRuntimeService.execute_async()` for creating and dispatching queued executions.
- Added `POST /workflows/{workflow_id}/execute-async`.
- Added `GET /workflow-executions/{execution_id}/status`.
- Preserved the existing synchronous `POST /workflows/{workflow_id}/execute` contract and behavior.
- Persisted workflow version is used by the worker rather than resolving the current active version at execution time.
- Queue payloads contain only `execution_id`; raw DataFrame, upload bytes, or other large payloads are not placed on the queue.
- No progress percentage, retry policy, worker metadata, or durable external queue was introduced in S14-A.

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

- S14-A Async Workflow Execution is complete and fully tested.
- Workflow executions can now be persisted as `QUEUED`, dispatched through an application queue port, atomically claimed by a background worker, and resumed through the existing `WorkflowEngine`.
- The existing synchronous workflow execution endpoint remains unchanged.
- The current queue implementation is intentionally in-process and is not durable across process restarts.
- No semantic progress percentage is exposed yet because S14-A does not define a reliable progress unit.
- Next sprint scope: S14-B streaming/chunked workflow execution and batch processing for large tabular datasets.

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
- The in-process workflow queue is not durable across process restarts and is intended as the minimal S14-A adapter.
- S14-A has no retry policy or dead-letter handling; failed executions are persisted as `FAILED`.
- Large-scale streaming/chunk execution is not yet integrated into the async worker path; this remains S14-B scope.

## Next Action

- Proceed to S14-B: streaming/chunked workflow execution and batch processing for large tabular datasets.
- Preserve the S14-A execution queue boundary and persisted `execution_id` contract.
- Do not introduce an external durable queue unless S14-B requirements demonstrate that the in-process adapter is insufficient.