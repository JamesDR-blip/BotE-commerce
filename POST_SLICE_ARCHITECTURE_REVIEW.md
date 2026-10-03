# Post-Slice Architecture Review

**Date:** 2026-10-02  
**Scope:** Read-only reassessment after the Application Memory Persistence Port and owner-scoped sync-job status route slices. No source/test execution or database verification was performed for this review. The accepted current suite evidence is 194 modules / 981 passed; the four-test increase over 977 is attributed to two regression tests per completed slice.

## Updated dependency graph

| Edge | Status | Current repository evidence |
|---|---|---|
| application → repositories | **Reduced** | `application.memory.memory_service` now types against `application.memory.ports`; the SQL adapter lives under `infrastructure.persistence`. Other direct imports remain in workspace, channels, datasets, workflows, audit, changesets, and lineage use cases. |
| application → services | **Unchanged** | Use cases still import authorization, compliance, and quota services. `services.container` remains the composition root. |
| api → repositories | **Reduced, not removed** | `api.routes.channels.get_sync_job` now delegates to `ChannelSyncService`; `api.routes.channels` still directly reads channel listing. Execution routes/dependencies and compatibility providers still import repositories. |
| api → services | **Unchanged** | Data routes/dependencies use data operations; risk route reaches the container; auth providers remain in `api.dependencies`. `api.main → services.container` is intentional composition. |
| capabilities → agents | **Unchanged** | Validation, QA and extraction capabilities still import agent implementations. |
| capabilities → services | **Unchanged** | `capabilities.cleaning` still imports `services.data_operations`. |
| repositories → application | **Unchanged** | `repositories.channels` imports `application.channels.credential_cipher`; this remains a confirmed reverse dependency. The memory compatibility module now forwards to infrastructure and no longer adds a repository-to-application edge. |
| infrastructure/persistence → application | **Newly exposed, intentional port dependency** | `infrastructure.persistence.agent_memory_repository` imports the application-owned `AgentMemoryPersistencePort` to satisfy the inward-defined contract. Verify direction/cycles if that adapter is further consolidated; current compatibility facade does not feed back into application. |
| agents → domain/application/infrastructure | **Unchanged** | Agent modules remain domain-facing; memory is injected as an application service. Neither slice moved provider construction into agents or made agents depend on persistence adapters. |
| execution → application/domain/infrastructure | **Unchanged** | Workflow execution continues to depend on domain contracts and observability infrastructure; it does not acquire a new application dependency from these slices. |

The sync-job route-specific repository bypass is **resolved**. The API package still has repository dependencies, including the retained `get_sync_job_repository` provider; do not classify the whole API edge as resolved. The application memory service's direct repository edge is **resolved**; concrete persistence is now behind the application port.

## Current canonical owners

| Concept | Current canonical owner evidenced in code | Boundary status |
|---|---|---|
| Memory persistence | `application.memory.ports.AgentMemoryPersistencePort`; SQL behavior in `infrastructure.persistence.agent_memory_repository`; `repositories.agent_memory` is a compatibility facade | Resolved for this slice; table/session behavior unchanged. |
| Channel sync jobs | `application.channels.ChannelSyncService` for use-case behavior; `domain.channel_sync` for types/state; repository for persistence | Owner-scoped read now goes through the use case. |
| Channel listing | No application query owner established; route still calls `ChannelRepository.list_for_owner` after workspace authorization | Uncertain boundary; a plausible bounded follow-up, not yet approved. |
| Datasets | Domain entities under `domain.studio`; `application.datasets` use cases; repository/DB own persistence | Split by responsibility; app-to-repository and legacy policy coupling remains. |
| Quality | `application.quality` owns use-case orchestration; domain quality owns primitives/rules; legacy validation/data-operation paths remain active | Consolidated canonical behavior is not established across all entrypoints. |
| Validation | No single owner across categories; `validators`, `domain/quality`, `domain/validation`, capabilities and plugins remain active | Uncertain category/plugin boundaries. |
| Execution | `execution` owns workflow/capability execution lifecycle; domain execution types own state/contracts | Existing workflow and worker semantics remain separate concerns. |
| Workflows | `domain.studio.workflow` owns definitions; `application.workflows` owns authoring/runtime use cases; `execution.workflow.engine` executes | Split by responsibility, not duplicate canonical owners. |
| Approval | `application.approval` use cases; `domain.approval` contracts | Current owner established. |
| Changesets | `application.changesets` use cases; `domain.changeset` contracts; persistence adapters store records | Current owner established; direct repository/service coupling remains. |
| Risk | `application.risk` use cases and `domain.risk`/`domain.risk_evaluation` types | API route's container coupling remains transitional. |
| Compliance | Domain policy/contracts plus `services.compliance` runtime behavior | Transitional; application consumers still depend on legacy service. |
| Audit | `application.audit` use case and `domain.audit` event; repository persists | Current behavior owner established; use case still imports repository. |
| Lineage | `application.lineage` use case and `domain.lineage` types; repository persists | Current behavior owner established; use case still imports repository. |
| Marketplace | `application.marketplace` use cases, `domain.marketplace` contracts, infrastructure adapters | Current split is coherent; no change from these slices. |
| Authorization | `domain.authorization` policy types plus `services.authorization` runtime service | Transitional. Do not name one exclusive owner until authorization behavior is extracted/proven. |
| Quota | `domain.quota` types plus `services.quota` enforcement | Transitional; application workflow/dataset consumers still use legacy service. |

## Remaining migration hotspots

| Candidate | Exact edge / target owner | Likely files and test surface | Compatibility, DB, risk and rollback | Why bounded / readiness |
|---|---|---|---|---|
| Channel listing query boundary | Current API route plus `ChannelRepository.list_for_owner`; no proven application query owner | `api/routes/channels.py`, `api/dependencies.py`, `application/workspace/project_service.py`, `application/channels/channel_sync_service.py`, `repositories/channels.py`, channel API/repository tests | Keep `get_channel_repository` callable. Existing repository/schema only; no Alembic/PostgreSQL dependency. Behavioral risk is containable, but ownership risk is unresolved. | The route is small and behavior/test evidence exists, but `WorkspaceProjectService` owns workspace access and `ChannelSyncService` owns sync execution. Neither has demonstrated catalog-query ownership; a dedicated one-method service currently lacks a second use case/consumer. **Do not implement until an owner is justified.** |
| Application audit persistence port | `application.audit.audit_service → repositories.audit_events` → application port + infrastructure adapter (physical target remains proposal) | `application/audit/audit_service.py`, `repositories/audit_events.py`, container wiring, audit service/repository/API tests | Preserve repository import path as facade if moved. No schema change; persistence semantics/transactions must remain. Medium; revert injection to prior repository. | One use case and one repository edge, but transaction, append/list, and audit integrity contracts must be pinned before selection. |
| Changeset query boundary | `application.changesets.query_service → repositories.changesets` → application port or a specifically owned query adapter | `application/changesets/query_service.py`, `repositories/changesets.py`, wiring, changeset/API tests | Keep repository and public API shapes. Existing DB schema only, no migration needed; parity/security risk medium-high due tenant filtering. Revert service injection. | Narrow query service, but owner filtering and signed snapshot semantics make it less ready than channel listing. |

These are ranked by migration readiness only. The first candidate is not authorization to execute it. Other edges that look small but are not ready: `capabilities.cleaning → services.data_operations` (clean/validate/report parity unresolved); app → authorization/compliance/quota services (policy/security behavior); repository → application credential cipher (secret handling and import compatibility); API execution repository bypasses (trace/state/report semantics); quality/validation consolidation (category and plugin parity unresolved); workflow/runtime consolidation (worker and recovery differences); and domain pandas/scikit-learn boundaries (numeric contract not proven).

## Compatibility surface to retain

- `repositories.agent_memory` re-export; tests and possible hidden importers may still use it.
- `api.dependencies.get_sync_job_repository`; regression coverage verifies it remains callable although the selected route no longer uses it.
- `api.dependencies.get_channel_repository`, still used by channel listing.
- `models.*`, root `main.py`, legacy `services.*`, validators/plugin fallback paths, `ai/`, dashboard launchers (`dashboard.py`, `app/dashboard.py`), and compatibility/provider entrypoints previously inventoried. This review has not proven external consumers absent; do not delete these paths.

## Database blocker separation

Both slices changed Python dependency routing only; they changed no database schema, Alembic history, startup, worker initialization, migration policy, or persisted behavior. Architectural consolidation remains distinct from production database takeover. Repository evidence in this reassessment does not change:

```text
PRODUCTION_SCHEMA_BASELINE = UNKNOWN
POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE
MIGRATION_REPAIR = BLOCKED
PHASE_5 = NO-GO
NEXT_SLICE_EXECUTION = NOT_AUTHORIZED
```

## Test baseline and decision

Accepted post-slice evidence: **194 test modules / 981 passed**, no failures, errors, skips, or warnings. The increase from **193 / 977** is the four regression tests added across the two slices (two each). The full suite was **not run for this reassessment**. Preserve the accepted result as reported; rerun only when an implementation slice is separately authorized.

**REASSESSMENT_COMPLETE** — the current graph, owners, residual hotspots, compatibility surface, and unchanged database blocker are bounded by repository evidence and the accepted test record. `NEXT_SLICE_EXECUTION = NOT_AUTHORIZED`.
