# PROJECT STATE

## Current Sprint

**S18 - ChangeSet & Atomic Rollback Engine — COMPLETE**

S18 is complete at code, test, architecture, persistence, API, and approval-integration level.

The production mutation boundary is now represented by immutable ChangeSets. Candidate artifacts are materialized before approval, production dataset pointers are changed only through transactional ChangeSet application, and rollback restores the prior immutable artifact pointer using optimistic concurrency protection.

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
- S14-A Async Workflow Execution
- Structural Refactor: Clean Architecture + DDD layers (`domain/`, `application/`, `execution/`, `infrastructure/`)

## Test Status

- **Test Suite:** `510 / 510 passing` via `python -m pytest`
- **Full Suite Execution Time:** approximately `24.5 seconds`
- **Warnings:** 1 existing Starlette/AnyIO TestClient deprecation warning.
- **S15 domain tests:** 5 passing.
- **S15 application-service tests:** 3 passing.
- **S15 API tests:** 5 passing.

## Database / Migration Status

- **Engine:** SQLite (local dev/test), PostgreSQL (production)
- **Current Database Revision:** `f3a4b5c6d7e8`
- **Repository Alembic Head:** `f3a4b5c6d7e8`
- **Migration State:** Local database is at c13a7e91d204; repository head is 20230912_04. Legacy clean-from-zero Alembic baseline remains a known limitation.
- **S15 Migration:** Added nullable `executions.dataset_id`, indexed and linked by foreign key to `datasets.id`.
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

## S15 Implementation

- Added multidimensional dataset health domain models:
  - Completeness
  - Validity
  - Uniqueness
  - Consistency
  - Timeliness
- Health aggregation ignores dimensions that are not currently assessed.
- Added sanitized `IssueDiagnostic` domain model.
- Added read-only `RemediationProposal` domain model.
- Added `DataHealthService` for project-scoped dataset health aggregation.
- Reused persisted dataset profile metadata for completeness and uniqueness signals.
- Reused persisted validation execution health scores for validity.
- Derived deterministic consistency scoring from persisted validation logs.
- Timeliness remains explicitly unassessed because no generic freshness/SLA signal exists yet.
- Added ownership-scoped health metrics API.
- Added sanitized dataset diagnostics API.
- Added Streamlit Data Health Command Center UI.
- Added remediation proposal preview without executing mutations.
- Added API, application, and domain regression coverage.

## S16 Implementation

- Added deterministic risk classification through RiskPolicy and RiskScore.
- Added ConfidenceScore and risk evaluation application service.
- Added persisted risk assessments.
- Added ApprovalRequest / ApprovalDecision lifecycle.
- Added hashed approval tokens; plaintext tokens are returned only at approval creation.
- Added approver-role authorization and token validation.
- Added PENDING_APPROVAL and CANCELLED workflow states.
- Integrated high/critical risk gating into workflow runtime.
- Approved executions return to QUEUED and resume through the existing worker.
- Rejected executions become CANCELLED.
- Wired DataHealthService confidence into production runtime.
- Added risk/approval API, repositories, migrations, and regression coverage.

### S18 Lifecycle Update

S18 supersedes the S16 approval-resumption behavior for ChangeSet-backed production mutations: approved high/critical executions now apply their prepared immutable ChangeSet atomically instead of returning to `QUEUED` for workflow re-execution. The legacy queue execution path remains available for non-ChangeSet execution flows.

### S17 Implementation

- Added domain simulation contracts:
  - SimulationResult
  - DiffPreview
  - TabularDiff
  - RowDiff
- Added ShadowExecutionRunner for isolated, ephemeral workflow simulation.
- Reused the existing CapabilityExecutionService and capability registry; no separate capability execution engine was introduced.
- Added SimulationService with owner-scoped workflow and dataset resolution.
- Added POST /workflows/{workflow_id}/simulate.
- Added owner/project-scope validation for simulation datasets.
- Added streaming simulation through read-only DatasetStorage.open() access.
- Added bounded-memory streaming diff aggregation.
- Added deep isolation of DataFrame, Series, and mutable auxiliary inputs.
- Simulation does not create or persist WorkflowExecution.
- Simulation does not persist execution traces.
- Simulation does not write dataset storage.
- Simulation does not create ChangeSets or mutate production state.
- Existing production WorkflowEngine execution behavior remains unchanged.
- No risk/approval boundary from S16 is bypassed.
- No Alembic migration was required.

## S18 Implementation

- Added immutable `ChangeSet` and `ChangeSetItem` domain models.
- Added `PREPARED`, `APPLIED`, and `ROLLED_BACK` lifecycle states.
- Added candidate artifact materialization with SHA-256 verification.
- Added positional row-level ChangeSet items based on the existing S17 diff identity model.
- Added `ChangeSetRepository` with owner-scoped queries.
- Added transactional Apply and Rollback operations.
- Added optimistic concurrency guards using the expected dataset storage key.
- Added `ChangeSetMutationService`.
- Added `ChangeSetRollbackService`.
- Added `ApprovalChangeSetService`.
- Integrated ChangeSet preparation into the high/critical risk approval path.
- Approval now applies the prepared ChangeSet atomically instead of requeueing the execution.
- Approval, ChangeSet Apply, and execution completion occur within one database transaction.
- Added ChangeSet list/detail/rollback APIs.
- Added approval → ChangeSet foreign-key integrity.
- Preserved the existing WorkflowEngine for computation/execution rather than making it responsible for production mutation.
- Production `DatasetRecord` mutation is restricted to the ChangeSet repository boundary.

### S17 Test Status

- Full regression: **546 / 546 passing** via python -m pytest.
- Full suite execution time: approximately **25.01 seconds**.
- Warnings: 1 existing Starlette/AnyIO TestClient deprecation warning.
- git diff --check: clean.

### S17 Known Constraints

- Streaming row diffs currently use positional row alignment rather than business-key matching.
- Simulation uses a bounded diff preview; the API currently relies on the default max_diff_rows limit.
- Simulation plan deserialization is currently implemented locally in SimulationService.
- The existing Starlette/AnyIO deprecation warning remains.

## Current Focus

- S17 Shadow Mode & Simulation is complete at code/test level.
- Simulation provides an isolated dry-run path without production execution persistence or dataset mutation.
- Streaming simulation uses read-only persisted dataset access and bounded-memory diff aggregation.
- Existing synchronous and asynchronous production execution paths remain backward compatible.
- S18 ChangeSet & Rollback is complete and is now the production mutation boundary.

## S15 Known Constraints

- Current health metrics are project-scoped through the existing project API boundary.
- Historical multidimensional health snapshots are not persisted yet.
- Category benchmark computation is not implemented yet.
- Remediation proposals are read-only and are not persisted as an approval/execution lifecycle.
- Timeliness is explicitly unassessed until a reliable freshness/SLA signal is available.
- The dashboard relies on the existing authentication boundary; production authentication remains a separate platform concern.
- Dashboard diagnostic loading currently performs per-dataset diagnostic requests.

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

## Next Action

S18 ChangeSet & Atomic Rollback Engine is complete.

Proceed to S19 Data Lineage & Audit.

S18 should introduce the explicit production mutation boundary required for deterministic ChangeSets, rollback, auditability, lineage, and HITL approval integration.

Future S15-adjacent improvements should be introduced only when justified by product requirements:
- historical multidimensional health snapshots,
- category benchmarks,
- persisted remediation lifecycle,
- richer timeliness/freshness signals.
