# S14 Sprint Handoff

## Status

S14 — Performance, Streaming & Asynchronous Workers: COMPLETE at code/test level.

S14-A asynchronous execution and S14-B streaming/chunked execution are both implemented and verified.

## Completed Work

### S14-A

- Persisted `QUEUED` workflow execution state.
- Application-level queue port.
- In-process worker.
- Execution-ID-only queue payload.
- Persisted workflow-version execution.
- Async execution and status APIs.
- Atomic execution claiming.

### S14-B

- Added nullable `workflow_executions.dataset_id`.
- Added dataset ownership validation.
- Added workflow/dataset project-scope validation.
- Added opt-in streaming execution in the existing `WorkflowEngine`.
- Reused persisted dataset storage and `StreamingTabularReader`.
- Processed tabular datasets chunk-by-chunk.
- Reused existing capability execution per chunk.
- Preserved synchronous workflow execution.
- Preserved the S14-A queue boundary.
- Added 100k-row benchmark coverage.

## Changed Files

- `api/routes/workflows.py`
- `application/workflows/runtime_service.py`
- `database/models.py`
- `database/migrations/versions/e2f3a4b5c6d7_add_workflow_execution_dataset.py`
- `execution/workflow/engine.py`
- `repositories/workflow_executions.py`
- `schemas/requests.py`
- `services/container.py`
- `tests/test_api_workflow_execution.py`
- `tests/test_streaming_reader.py`
- `tests/test_workflow_engine.py`
- `tests/test_workflow_execution_async_state.py`
- `tests/test_workflow_runtime_service.py`
- `data_quality.db`

## Tests

- S14-B targeted regression: 47 passed.
- Full regression: 495 passed.
- Runtime: approximately 24.8 seconds.
- 1 existing Starlette/AnyIO deprecation warning.

## Migration

`e2f3a4b5c6d7_add_workflow_execution_dataset.py`

Revision:

`d14c1f2a9b31 -> e2f3a4b5c6d7`

Changes:

- nullable `workflow_executions.dataset_id`
- foreign key to `datasets.id`
- index `ix_workflow_executions_dataset_id`

Current database and repository are both at `e2f3a4b5c6d7`.

## Architecture Decisions

1. Reuse `WorkflowEngine`; do not create a second streaming engine.
2. Reuse existing dataset storage and streaming reader abstractions.
3. Reuse existing capability execution for each chunk.
4. Persist dataset identity rather than queueing raw data.
5. Preserve execution-ID-only async queue payloads.
6. Keep `dataset_id` nullable for backward compatibility.
7. Make streaming execution opt-in through existing execution-plan metadata.
8. Do not introduce a durable/distributed queue without deployment-driven justification.

## Security / Safety

- No `eval`, `exec`, unsafe YAML, pickle, or arbitrary SQL introduced.
- Queue payloads do not contain raw data.
- Dataset/workflow ownership is enforced.
- Dataset and workflow must belong to the same project.
- Existing risk, approval, ChangeSet, and confidence boundaries are unaffected.

## Known Issues

- In-process queue is not durable.
- No retry/dead-letter infrastructure.
- No generic semantic progress percentage.
- Individual capabilities may have capability-specific memory behavior.
- `tracemalloc` benchmark is not an OS RSS measurement.
- Existing Starlette/AnyIO deprecation warning remains.

## Remaining Work

- Evaluate durable/distributed queue infrastructure for production deployment.
- Define retry/dead-letter semantics if durable workers are introduced.
- Define reliable progress semantics before exposing progress percentage.

## Recommended Next Steps

1. Keep S14-A/S14-B behavior stable.
2. Monitor large-dataset execution characteristics.
3. Evaluate production queue requirements based on actual deployment topology.
4. Address the Starlette/AnyIO dependency warning through dependency maintenance.