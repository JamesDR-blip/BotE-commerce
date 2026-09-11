# PROJECT STATE

## Current Sprint

**S14 - Performance, Streaming & Asynchronous Workers**

S14-A and S14-B are complete at code/test level.

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

- **Test Suite:** `495 / 495 passing` via `python -m pytest`
- **S14-B targeted regression:** `47 / 47 passing`
- **Full Suite Execution Time:** ~24.8 seconds
- **Warnings:** 1 dependency deprecation warning from Starlette/AnyIO TestClient.

## Database / Migration Status

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Current Database Revision:** `e2f3a4b5c6d7`
- **Repository Alembic Head:** `e2f3a4b5c6d7`
- **Migration State:** Database is synchronized with repository head.
- **S14-B Migration:** Added nullable `workflow_executions.dataset_id`, indexed and linked by foreign key to `datasets.id`.
- Existing executions remain compatible because `dataset_id` is nullable.

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

## S14-B Implementation

- Added persisted dataset references to workflow executions.
- Added ownership and project-scope validation for workflow/dataset execution requests.
- Preserved the S14-A execution-ID queue boundary.
- Extended the existing `WorkflowEngine` with opt-in streaming execution through execution-plan metadata.
- Streaming execution reloads the persisted dataset and opens its persisted source through `DatasetStorage`.
- Tabular input is processed chunk-by-chunk through the existing `StreamingTabularReader`.
- Existing capability execution is reused for each chunk; no separate streaming workflow engine was introduced.
- Chunk execution does not accumulate the complete dataset in the worker execution loop.
- Added 100k-row streaming benchmark coverage.
- Verified 100k rows using 10 chunks of 10,000 rows with a Python-allocation ceiling assertion below 512 MB.
- The memory benchmark uses `tracemalloc` as a Python allocation proxy; it is not an OS RSS measurement.
- Async execution remains compatible with S14-A because queued messages continue to contain only `execution_id`.

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

- S14 Performance / Streaming & Asynchronous Workers is complete at code/test level.
- S14-A provides persisted asynchronous workflow execution through the execution-ID queue boundary.
- S14-B provides opt-in chunked execution over persisted tabular datasets.
- Synchronous workflow execution remains backward compatible.
- The in-process queue remains intentionally minimal and non-durable.

## Known Constraints

- The in-process workflow queue is not durable across process restarts.
- S14-A has no retry policy or dead-letter handling; failed executions are persisted as `FAILED`.
- No semantic progress percentage is exposed because there is not yet a reliable generic progress unit.
- Streaming execution is opt-in through workflow execution-plan metadata.
- Individual capabilities may still have capability-specific memory behavior; S14-B bounds the workflow's tabular input handling rather than guaranteeing constant memory for arbitrary capability internals.
- The 100k-row memory verification uses `tracemalloc`, not process RSS.
- Production-scale durable/distributed queue infrastructure remains a future deployment decision.

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

- Evaluate production queue durability, retry, dead-letter, and worker lifecycle requirements before production-scale deployment.
- Continue future performance work only where measurements demonstrate a bottleneck.
- Preserve the execution-ID queue boundary and persisted workflow-version semantics.