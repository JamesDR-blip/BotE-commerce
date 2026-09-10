# ENGINEERING RULES

## General

1. Inspect existing code before creating new abstractions.
2. Reuse existing services/capabilities where possible.
3. Avoid duplicate business logic.
4. Keep changes small and reversible.
5. Do not introduce breaking changes without justification.

## Domain Layer (`domain/`)

- Must remain completely framework independent.
- No database imports (no SQLAlchemy, Alembic, SQLite, Postgres).
- No HTTP or web framework imports (no FastAPI, Starlette, Requests, Httpx).
- No LLM provider or orchestration framework imports (no Google GenAI, LangChain, LangGraph).
- Domain models and value objects must contain validation logic and core business invariants.

## Application Layer (`application/`)

- Business use cases and orchestration live here.
- Coordinates domain services and repositories.
- Manages transactional boundaries and ownership permissions (e.g. Workspace owner scoping).
- Must not depend directly on presentation frameworks (FastAPI/Streamlit).

## Execution Layer (`execution/`)

- Responsible for workflow state machines, capability scheduling, parameter resolution, and tracing.
- Executes capabilities against execution plans; handles step failures, partial traces, and terminal states (`COMPLETED`, `FAILED`).
- Interacts with capabilities strictly via `CapabilitySpec` and domain contracts.

## Infrastructure Layer (`infrastructure/`, `database/`, `repositories/`)

- Implements technical concerns: in-memory caching (`TTLCache`), tabular parsing (`TabularUploadReader`), JSON logging, database persistence.
- Implements repositories defined by application interfaces (Dependency Inversion).
- Enforces security boundaries: formula escaping in spreadsheets, request body size limits, path containment for stored reports/artifacts.

## Agents Layer (`agents/`)

Agents may reason and propose operations.

Agents may NOT:
- directly modify database records
- bypass validation or execution engines
- bypass risk policy or approval mechanisms
- execute arbitrary code or shell commands
- execute arbitrary SQL

## LLM Inference

- LLM output must always be validated against Pydantic schemas or domain contracts.
- LLM is used strictly for semantic reasoning, explanations, and suggested fixes; never for arbitrary code execution.
- Minimize and redact sensitive data sent to external models.

## Testing

- Every new behavior requires automated unit or integration tests.
- Regression tests must remain green across all layers.
- Test suites must be runnable via `pytest` without side-effects on persistent environments.

## Security

Never use:
- `eval()`
- `exec()`
- unsafe deserialization (e.g. `pickle.loads`)
- unsafe YAML loading (always use `yaml.safe_load`)
- unescaped arbitrary SQL queries
- unvalidated tool calls
- unescaped spreadsheet cell values on export
