# Architecture Inventory — Discovery Baseline

**Scope:** read-only repository inventory, refreshed 29 September 2026. No application source, tests, database migrations, or runtime configuration were changed. The only current tracked-code state is clean on branch `main`; the five discovery documents are local untracked deliverables.

## Protected baseline evidence

- Baseline accepted for this work: **977 tests passed**.
- Direct full-suite run recorded in this conversation: `python -m pytest -q`, **977 passed in 64.27 seconds**. This was completed with filesystem access for pytest temporary directories after sandboxed attempts failed during temp-directory setup/cleanup.
- Repository evidence agrees on count: `SPRINTS/sprint-28-hardening.md` records 977 passed and 3 warnings; `HANDOFF/CURRENT_STATE.md` records 977/977 via `python -m pytest`, 104.72 seconds, 3 warnings. Durations differ between recorded runs; count agrees.
- Current `tests/` contains 193 `test_*.py` modules. The full suite was **not rerun in this documentation-only refresh**. Treat 977 as a protected regression gate; any changed collection needs an explicit explanation and review.

## Repository shape

The checkout is a single Python repository with top-level layers rather than a `src/platform` package. The inventory below counts Python files recursively and excludes bytecode caches; it describes physical placement, not correctness of ownership.

| Area | Python files | Observed role |
|---|---:|---|
| `domain/` | 63 | Data-quality primitives plus identity, org/RBAC concepts, catalog, capability metadata/dependencies, plans, execution, Studio, workflow, governance, channels, marketplace, memory, lineage |
| `application/` | 45 | Use cases for workspaces, datasets, quality, workflow authoring/runtime/history/simulation, autonomous operations, approvals, changesets, audit, lineage, risk, rules, channels, copilot, marketplace, memory |
| `infrastructure/` | 27 | Upload and dataset storage, cache, Redis/in-process queues, SQL-related adapters, channels, marketplace package handling, Chroma rule retrieval, credential encryption, telemetry/logging |
| `api/` | 20 | FastAPI factory, dependencies, schemas adapter, and route modules |
| `repositories/` | 23 | SQLAlchemy-backed repositories for platform aggregates and records |
| `services/` | 8 | Composition root and older authentication/authorization/compliance/quota/data-operation/validation services |
| `database/` | 26 | SQLAlchemy records, session factory, Alembic environment and migration history |
| `agents/` | 13 | Intent, requirement, planning, extraction, rule retrieval, QA, report, workflow collaborators, optional LLM assistant |
| `execution/` | 7 | Workflow engine/worker, capability execution, execution context, plan validation, traces, shadow runner |
| `capabilities/` | 5 | Cleaning, extraction, normalization, QA, validation implementations |
| `tests/` | 193 test modules | API, domain, application, integration, persistence, security, capability, workflow, migration-adjacent and property/fuzz coverage |

Other active areas include `plugins/`, `validators/`, `rule_engine/`, `extractors/`, `reports/`, `configs/`, `views/`, `controllers/`, `models/`, `schemas/`, `app/`, `docs/`, `SPRINTS/`, `HANDOFF/`, and `AI_CONTEXT/`. `chroma/`, `artifacts/`, reports, local SQLite data and test/cache directories are runtime or generated data and should not be treated as source architecture.

## Runtime and entrypoints

- `api/main.py:create_app` is the FastAPI application factory. It configures logging/telemetry, builds `services.container.Container`, registers route modules, and exposes many composed dependencies through `app.state`.
- `app/main.py` builds settings and the API app for the `app` runtime entrypoint. Root `main.py` re-exports `create_app` for compatibility. README also documents `uvicorn api.main:create_app --factory`.
- `worker.py` builds the same container and runs the Redis-backed workflow consumer; it rejects a non-Redis queue configuration.
- Root `dashboard.py` / `app/dashboard.py` and `app/api_client.py` support the Streamlit UI. README says the dashboard talks to the API over HTTP; confirm its current wiring before changing that contract.
- `docker-compose.yml`, `docker-compose.prod.yml`, `Dockerfile`, and `nginx/` describe local/production containers, worker, reverse proxy and supporting services. S26 handoff reports Docker runtime validation and production telemetry/alerting as pending external checks.

## Persistence and configuration

- SQLAlchemy records are canonical in `database/models.py`; repositories in `repositories/` use those records. `models/database.py` and `models/domain.py` are compatibility re-exports; nested `models/` packages and `models/repositories` also remain and require per-module reference classification.
- Alembic lives under `database/migrations/`; `alembic heads` reports one head, `20260928_01`. There are 23 version files, including older hash-prefixed revisions and newer dated revisions. README agrees with this head.
- `database.models.make_session_factory` calls `Base.metadata.create_all(engine)`. Thus schema creation still occurs outside Alembic at application/container startup and is a material persistence boundary to resolve without losing local/test compatibility.
- `configs/`, `.env.example`, `alembic.ini`, compose files and `requirements.txt` define runtime configuration. A local `.env` exists and was not read or included in this inventory.
- Declared dependencies match FastAPI/Starlette/Uvicorn, Streamlit/Plotly, pandas/OpenPyXL/PyYAML/scikit-learn, SQLAlchemy/Alembic/PostgreSQL, Google GenAI/Chroma/Sentence Transformers, Redis/HTTPX/cryptography, OpenTelemetry/Prometheus, pytest/Hypothesis.

## Existing architecture documentation and evidence quality

- `README.md` describes the richer AI Studio / data operations product and current directory roles; its dependency flow is an aspirational simplification in places.
- `docs/` contains API, deployment, developer and operator documentation from S27.
- `ARCHITECTURE_AUDIT.md` describes a much smaller data-quality application and says studio/workflow/migration capabilities are absent. It is stale relative to current routes, modules, migrations and S27/S28 sprint records.
- `SPRINTS/` includes records through S28; `HANDOFF/CURRENT_STATE.md` reports core S28 complete, with external pen testing, deployment runtime, telemetry/alerting follow-up outstanding.
- Tests and current code are the behavior evidence. Sprint completion claims and documentation require verification against code, and are not treated as proof of production readiness.

## Established implementation anchors

These are strong existing candidates to retain as canonical owners during migration, subject to call-site and test preservation:

1. `domain/` for business types and rules, with exceptions noted in `DEPENDENCY_MAP.md`.
2. `application/` for platform use cases, while replacing concrete legacy-service/repository imports incrementally.
3. `database/models.py` + Alembic for canonical persistence schema/history; `repositories/` for storage access.
4. `execution/workflow/engine.py` and `application/workflows/runtime_service.py` as the current workflow engine and use-case boundary, with the worker queue as delivery mechanism.
5. `domain.capability_registry` + `execution/capabilities/` + `capabilities/` for registration, execution orchestration and implementations respectively.
6. `infrastructure/` for technical adapters, although some application modules still construct or import concrete adapters.
7. `api/routes/` for HTTP endpoint adapters and `app/` for runtime/dashboard entrypoints.

## Discovery limitations

Local state may differ from CI. This inventory did not validate external PostgreSQL, Redis, provider credentials, Docker deployment, production telemetry exporters, or live marketplace/channel endpoints. `WORKFLOW`, quality and legacy owners listed here are code-level candidates; consumer and test mappings in `MIGRATION_PLAN.md` determine whether an individual migration is ready.

## Post-slice status correction (2026-10-02)

The inventory above is the original Phase 0 discovery snapshot, not a current statement that the worktree is clean or that the 977 baseline is the latest suite result. Two bounded code slices have since completed: Application Memory Persistence Port and owner-scoped sync-job status route. Accepted current evidence is **194 test modules / 981 passed**; the four additional tests are two regression tests per slice. The full suite was not rerun during this reassessment. See `POST_SLICE_ARCHITECTURE_REVIEW.md` for current dependency and ownership deltas. These slices did not change database schema, Alembic, startup, or production database evidence; Phase 5 remains NO-GO.
