# CURRENT STATE

**Project:**
AI Studio E-commerce Platform

**Product:**
Autonomous E-commerce Data Operations Platform

**Current Sprint:**
S14 — Performance, Streaming & Asynchronous Workers: COMPLETE at code/test level.

**Last Completed:**
S14-B — Streaming / Chunked / Batch Workflow Execution.

**Architecture:**
Clean Architecture + DDD (Domain, Application, Execution, Infrastructure, Presentation)

**Composition Root:**
`services/container.py`

**Tests:**
495 / 495 passing via `python -m pytest`.

**Targeted S14-B Regression:**
47 / 47 passing.

**Database:**
- Current database revision: `e2f3a4b5c6d7`.
- Repository Alembic head: `e2f3a4b5c6d7`.
- Database is synchronized with repository head.

**Current Work:**
S14-A introduces asynchronous workflow execution while preserving the existing synchronous execution path. Workflow executions can be persisted as `QUEUED`, dispatched through an application-level queue port, atomically claimed by a background worker, and resumed through the existing `WorkflowEngine`.

The async worker receives only the persisted `execution_id`. It reloads the persisted workflow execution and workflow version before execution, preventing raw DataFrame/upload payloads from being placed on the queue and ensuring execution uses the version that was persisted when the execution was created.

**Key S14-A Properties:**
- `QUEUED` is a persisted workflow execution state.
- Queue access is defined through an application `WorkflowExecutionQueue` port.
- The current infrastructure adapter is an in-process background queue.
- Queue payloads contain only `execution_id`.
- `QUEUED -> RUNNING` is claimed atomically to prevent duplicate execution.
- The worker reuses the existing `WorkflowEngine`; no separate async engine was introduced.
- The persisted workflow version is used instead of resolving the current active version at worker execution time.
- Existing synchronous workflow execution remains backward compatible.
- Async execution is exposed through `POST /workflows/{workflow_id}/execute-async`.
- Execution status is exposed through `GET /workflow-executions/{execution_id}/status`.
- No progress percentage, retry policy, worker metadata, or durable external queue was introduced in S14-A.

## S14-B Completed Work

- Workflow executions can persist an optional dataset reference.
- Dataset ownership and workflow-project scope are validated before execution.
- `WorkflowEngine` supports opt-in streaming execution using persisted datasets.
- CSV/XLSX sources are read chunk-by-chunk.
- Existing capability execution is reused per chunk.
- The complete dataset is not accumulated by the streaming workflow execution loop.
- S14-A's execution-ID-only queue contract is preserved.
- 100k-row benchmark coverage was added.

**Key Safety Properties:**
- Queue payloads do not contain raw DataFrame or upload bytes.
- Workflow execution remains behind the existing application/execution boundaries.
- The domain layer remains framework-independent.
- The worker cannot bypass persisted workflow execution state.
- Atomic execution claiming prevents the same queued execution from being claimed twice.
- Existing ChangeSet, approval, risk, and confidence boundaries remain unaffected.
- No `eval`, `exec`, `pickle`, or unsafe YAML loading was introduced by S14-A.

**Blocking Issues:**
None.

## Known Considerations

- The in-process queue is not durable across process restarts.
- Retry and dead-letter handling are not implemented.
- A generic semantic progress percentage is not exposed.
- Streaming mode is opt-in through execution-plan metadata.
- Individual capabilities may have their own memory characteristics.
- The 100k-row memory test uses `tracemalloc`, not OS RSS.
- Durable/distributed queue infrastructure remains a production deployment evaluation rather than S14-B implementation scope.
- The existing Starlette/AnyIO TestClient deprecation warning remains.

## Next Action

Evaluate production deployment requirements for queue durability, retry, dead-letter handling, worker lifecycle, and progress semantics before introducing additional infrastructure.