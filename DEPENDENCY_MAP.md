# Dependency Map — Observed Imports

**Method:** static AST scan of Python imports under the named source packages, followed by inspection of composition and representative route/service modules. Counts below are import statements between package roots, not runtime call frequency. Dynamic imports and plugin discovery may add edges. This is an observed graph, not a claim that every edge is architectural API.

## Intended direction

```text
API / dashboard / worker interfaces
                 ↓
             application
                 ↓
               domain

Infrastructure adapters ──implement/use──> application ports and domain types
Composition root wires interfaces, use cases, adapters, repositories and workers.
```

## Observed package-level edges

| Importer | Observed internal imports | Assessment |
|---|---|---|
| `domain` | Internal domain modules; pandas (9 imports), scikit-learn (1), packaging and general libraries | No imports from infrastructure/API/database/services were found in this scan. Framework independence is partial: domain quality modules depend on dataframe/ML libraries. |
| `application` | domain (51), repositories (18), services (12), agents (4), infrastructure (3), rule_engine (3), execution (1), database (1) | Most serious boundary leakage. Application depends on concrete repositories and legacy services; selected use cases reach agents, execution engine, infrastructure and ORM records. |
| `api` | application (35), domain (19), schemas (18), repositories (8), services (6), infrastructure (4), agents (2) | Routes mostly use application use cases, but direct persistence, legacy service, technical adapter, agent and domain dependencies remain. |
| `services` | application (29), repositories (24), infrastructure (20), domain (18), agents (8), capabilities (5), execution (4), plugins/validators/extractors/rule_engine | `services.container` is a broad composition root; other service modules retain business behavior and have dependencies crossing several layers. |
| `capabilities` | domain (8), agents (4), services (1), extractors (1), plugins (1) | Capability implementations use domain contracts but also directly depend on agents, legacy data operations and plugin registry. |
| `repositories` | database (21), domain (13), rule_engine (2), application (1) | SQL persistence is appropriately localized, except channel repository imports `application.channels.credential_cipher`, reversing ownership. |
| `execution` | domain (18), infrastructure (2) | Mostly directional, with observability infrastructure imported directly. |
| `agents` | domain (22), rule_engine (2), extractors (1), plus internal agent imports | Mostly core-facing; external AI provider usage lives in `agents/llm.py` and application/copilot modules, requiring an explicit provider port boundary. |
| `plugins` / `validators` | Cross-import each other; rule_engine and domain | Validator plugin discovery still falls back to the older validators package, so both extension surfaces are live. |

## Concrete coupling and cycle candidates

### Complete direct importer census for the application/API seams

This table enumerates every direct import found by AST under `application/` and `api/` whose root is `services` or `repositories`. Counts are per importing file, not import statements. `services.container` at `api.main` is composition; provider modules and route-level implementation imports are separate edges.

| Importer | Direct targets |
|---|---|
| `application/approval/approval_service.py` | `services.authorization` |
| `application/audit/audit_service.py` | `repositories.audit_events` |
| `application/changesets/mutation_service.py` | `services.compliance` |
| `application/changesets/query_service.py` | `repositories.changesets` |
| `application/channels/canonical_product_service.py` | `repositories.datasets` |
| `application/channels/channel_sync_service.py` | `repositories.channel_mappings`, `repositories.channels`, `repositories.datasets`, `repositories.projects`, `repositories.sync_jobs` |
| `application/datasets/dataset_service.py` | `repositories.datasets`, `repositories.projects`, `repositories.workspaces`, `services.authorization`, `services.compliance`, `services.quota` |
| `application/lineage/lineage_tracking_service.py` | `repositories.data_lineage_events` |
| `application/memory/memory_service.py` | `repositories.agent_memory` |
| `application/workflows/authoring_service.py` | `repositories.projects`, `repositories.workflows`, `repositories.workspaces`, `services.authorization` |
| `application/workflows/history_service.py` | `services.authorization` |
| `application/workflows/runtime_service.py` | `services.authorization`, `services.compliance`, `services.quota` |
| `application/workflows/simulation_service.py` | `services.authorization` |
| `application/workspace/project_service.py` | `repositories.projects`, `repositories.workspaces`, `services.authorization` |
| `api/dependencies.py` | `repositories.channels`, `repositories.execution_traces`, `repositories.executions`, `repositories.sync_jobs`, `services.authentication`, `services.authorization`, `services.data_operations` |
| `api/main.py` | `services.container` (composition root) |
| `api/routes/channels.py` | `repositories.channels`, `repositories.sync_jobs` |
| `api/routes/data.py` | `services.data_operations` |
| `api/routes/executions.py` | `repositories.execution_traces`, `repositories.executions` |
| `api/routes/risk.py` | `services.container` |

The list is current static evidence. It does not include dynamically loaded plugins, implicit runtime service-locator access via `request.app.state.container`, or imports outside these roots. Those are explicit Phase 0 call-site checks below.

Direct `application -> repositories` edges are confirmed boundary violations under the target rule. Direct application imports of authorization/compliance/quota are transitional coupling around live policy behavior. Route-injected repository instances are API bypasses. `api.main -> services.container` is intentional outer composition; `api.routes.risk -> services.container` is transitional route coupling.

1. **Application ↔ services:** `services/container.py` imports and assembles application classes. Application use cases import `services.authorization`, `services.compliance`, and `services.quota`. The container edge itself is composition, but the use-case imports mean decomposition has not removed the coupling.
2. **Application → repositories and database:** datasets/workflows and other use cases construct against repository classes directly; `application/quality/quality_service.py` imports `database.models.ExecutionRecord`. This bypasses ports and makes testing/storage replacement harder.
3. **API → persistence/legacy/core implementation:** exact service/repository importers are enumerated above. `api/routes/executions.py` uses repositories directly; channel routes use repositories for channel/sync-job queries; risk routes use the service container; data routes use `DataOperationsService`. `api.dependencies` also provides concrete authentication/authorization services, legacy data operations and four repositories. API-to-domain/schema dependencies are intentional interface mapping; concrete infrastructure/agent imports are a separate transitional boundary.
4. **Capabilities → service layer:** `capabilities/cleaning.py` imports `services.data_operations`, while the container wires capabilities and services together. This preserves the older service layer inside the purported capability path.
5. **Persistence → application:** `repositories/channels.py` imports `application.channels.credential_cipher`; the credential cipher contract should have one owner in domain/application ports or infrastructure security.
6. **Application → concrete adapters and execution:** `application/channels/canonical_product_service.py` imports infrastructure storage/upload classes; `application/quality/quality_service.py` invokes execution capability service. Their use-case and adapter/runner responsibilities need characterization before extraction.
7. **Domain → data/ML libraries:** `domain` imports pandas and scikit-learn. Determine whether these are domain calculations or dataframe adapter work; migrate only after behavior and public type expectations are clear.
8. **Two workflow implementations at different levels:** workflow authoring/runtime/history are use cases; `execution.workflow.engine` runs plans and has a worker. Redis and in-process queues are delivery adapters, not competing business runtimes. Treat them as one pipeline and verify exact data/state semantics before consolidation.
9. **Legacy aliases:** `models.*` are explicit compatibility imports; root `main.py` is also a compatibility entrypoint. Retain them until external/internal references and tests are inventoried.

## Architectural cycle status

The source brief reports application/services cycles; static imports confirm the two-way dependency path via use-case imports and the composition root. Package-level imports do not prove a Python runtime circular import, and none is asserted here. No automated circular-import detector was part of discovery. A follow-up should build a file-level dependency graph, classify composition-root edges separately, and run import/startup validation after each migration slice.

## Rules for the migration

- Keep the composition root at an outer boundary; do not move it into domain or use-case packages.
- Introduce small application-owned ports where use cases need storage, authorization, quota, compliance, queue, or provider behavior; implement them with current adapters.
- Make APIs call use cases and map request/response contracts; move repository lookups behind use cases where public route behavior can be preserved.
- Move legacy behavior by ownership, not folder name. `services.container` can remain as a temporary composition shim while service responsibilities are relocated.
- Keep domain free of FastAPI, SQLAlchemy, Redis, Streamlit, infrastructure and provider imports. Decide separately whether pandas/scikit-learn are acceptable domain primitives or adapter details.
- Treat plugin loading and AI-generated outputs as explicit extension/provider boundaries; preserve allowlisting, deterministic authorization, and current result contracts.

## Unresolved boundaries

- Runtime call sites using `request.app.state.container` are not visible as package imports; enumerate each before moving a service from the container.
- `dashboard.py` and `app/dashboard.py` wiring needs direct inspection before classifying any service/repository bypass there.
- `application.quality.quality_service` imports ORM, agents and execution; `application.copilot` reaches agents/telemetry; channel product projection reaches concrete storage/upload. Port ownership and consumer sets for these edges remain provisional.
- `domain` uses pandas/scikit-learn. Determine whether the relevant values/calculations are domain policy or dataframe-specific computation before relocating anything.
- `ai/`, nested `models/*`, `controllers/`, `views/` and external importers need reverse-reference/deployment evidence before deprecation or file moves.
- A package-level two-way path through application and the composition root is not proof of a Python import-time cycle. No runtime circular-import failure is established.

## Post-slice graph delta (2026-10-02)

The package counts and importer census above describe the pre-slice snapshot. Current import inspection confirms:

- `application.memory.memory_service` no longer imports `repositories.agent_memory`; it depends on `application.memory.ports`. The SQL adapter is now `infrastructure.persistence.agent_memory_repository`, and the old repository path forwards to it.
- `api.routes.channels.get_sync_job` no longer imports or injects `SyncJobRepository`; it delegates to `ChannelSyncService.get_sync_job`. The API still imports `repositories.channels` for channel listing, and `api.dependencies` retains the sync-job repository provider as a compatibility surface.
- `infrastructure.persistence.agent_memory_repository → application.memory.ports` is a newly exposed implementation-to-port dependency. It is intentional; the composition root still wires the adapter.
- All other listed app→repository/service, API→repository/service, capability→agent/service, and repository→application edges remain unless stated above. In particular `repositories.channels → application.channels.credential_cipher` remains.

Re-assessed graph, classifications and candidate slices: `POST_SLICE_ARCHITECTURE_REVIEW.md`. This delta narrows two specific edges; it does not clear the broader package-level boundaries or change the database takeover gate.
