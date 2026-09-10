# SPRINT 14: Performance, Streaming & Asynchronous Workers

## Status
Backlog

## Objective
Scale tabular processing to handle 100k+ row datasets without blocking HTTP workers by introducing streaming chunked ingestion, batch capability execution, and background worker queues.

## Architectural Layer Impact
- **Infrastructure Layer (`infrastructure/`):**
  - `infrastructure/upload/streaming_reader.py`: Chunked CSV/Excel reader with memory bounds.
  - `infrastructure/queue/`: Background task queue adapter (Celery / Redis Queue / Async worker).
- **Execution Layer (`execution/`):**
  - Chunked execution runner in `WorkflowEngine`.
  - Batch capability invocation.
- **Application Layer (`application/workflows/`):**
  - Async job dispatch in `WorkflowRuntimeService`.
- **API Layer (`api/routes/workflows.py`):**
  - `POST /workflows/{id}/execute-async`: Returns `execution_id` immediately.
  - `GET /workflow-executions/{id}/status`: Polling and progress tracking endpoint.

## Security & Constraints
- Strict memory ceiling (e.g. max 512MB RAM per worker during chunking).
- Task queue payload must reference persisted dataset IDs, never raw dataframe bytes.

## Verification Criteria
- Benchmark test processing 100k rows under memory ceiling.
- End-to-end async workflow execution and status polling test.
