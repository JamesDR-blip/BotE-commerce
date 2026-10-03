# Ownership Map — Current and Proposed Canonical Owners

Status labels in this discovery: **ACTIVE** means current production/test code uses the area; **TRANSITIONAL** means it is active but overlaps or violates the intended boundary; **COMPATIBILITY** means a shim/legacy surface kept for callers; **UNVERIFIED** means inventory cannot establish runtime ownership from static placement alone. No module is classified unused or approved for deletion in discovery.

## Canonical concept owners

This table is authoritative for the **single proposed owner of each concept contract**. Runtime coordinators, repositories, API schemas and provider adapters can consume or implement a contract; they do not create a second owner for that concept. Existing paths are evidence and preferred candidates, not permission to move files. Any path labeled proposed remains unproven until Phase 0 maps its consumers and tests.

| Concept | One proposed canonical contract owner | Current evidence / boundary note |
|---|---|---|
| Identity | `domain/identity.py` | User/current-identity value contract. |
| Authorization / RBAC | `domain/authorization.py` | Authorization concepts and policy; application use case evaluates it. |
| Organization | `domain/organization.py` | Organization concept; repositories persist records. |
| Quota | `domain/quota.py` | Dimensions/rules; service performs usage checks. |
| Workspace | `domain/studio/workspace.py` | Workspace entity. |
| Project | `domain/studio/project.py` | Project entity. |
| Dataset | `domain/studio/dataset.py` | Dataset entity; ingestion/profile/storage are separate operations. |
| Catalog / mapping | `domain/catalog/mapping.py` | Mapping model/service concept; channel persistence is an adapter. |
| Data quality | `domain/quality/` | Health, score and anomaly concepts; application owns orchestration. |
| Validation | `domain/validation/` | Reusable validation primitives; category extension contract belongs to plugins. |
| Capability | `domain/capabilities.py` | Capability contract/value types. |
| Capability dependencies | `domain/capability_dependency.py` | Dependency contract/version requirements. |
| Capability execution result | `domain/capability_execution.py` | Execution result contract; dispatch and implementation are separate. |
| Requirement | `domain/requirement.py` | Typed workflow requirement. |
| Intent | `domain/intent_resolver.py` | Intent domain contract; classifier is a consumer. |
| Execution plan | `domain/plans.py` | Plan and step contracts. |
| Execution context | `domain/execution_context.py` | Context contract. |
| Execution trace | `domain/execution_trace.py` | Trace contract; collector and persistence are mechanisms. |
| Workflow | `domain/studio/workflow.py` | Workflow definition. |
| Workflow execution state | `domain/studio/runtime.py` | Workflow execution state/value contract; engine runs it. |
| Autonomous operations | `domain/autonomous_operations.py` | Autonomous policy/decision contract; application orchestrates. |
| Approval | `domain/approval.py` | Request and decision contracts. |
| ChangeSet | `domain/changeset.py` | ChangeSet and item snapshot contracts. |
| Rollback | `application/changesets/rollback_service.py` | Rollback operation is a use case; no separate rollback entity is evidenced. |
| Risk | `domain/risk.py` | Risk score/decision contracts. |
| Compliance | `domain/compliance.py` | Compliance policy concepts; application evaluates them. |
| Audit | `domain/audit.py` | Audit-event/hash-chain contract. |
| Lineage | `domain/lineage.py` | Lineage-event contract. |
| Channel synchronization | `domain/channel_sync.py` | Channel/sync-job contracts; adapters perform external IO. |
| Marketplace | `domain/marketplace.py` | Package/type contracts. |
| Executable rules | `rule_engine/models.py` | Typed rule schema/AST; use cases retrieve/evaluate through explicit services. |
| Plugins | `plugins/base.py` | Validator plugin contract; `plugins/registry.py` is discovery mechanism. |
| Agent memory | `domain/agent_memory.py` | Memory/correction/learning concepts. |
| Copilot | `application/copilot/` | Copilot application behavior; model/provider is a consumer. |
| Studio | `domain/studio/` | Studio aggregate/value contracts; use cases act on them. |
| Observability | `infrastructure/observability/` | Technical logs/metrics/traces; business audit is owned separately by `domain/audit.py`. |

Several owners are directories or use-case packages because the concept already spans cohesive modules or is an operation rather than a domain entity. This is a **logical owner map**; it does not assert that every type should be moved to a new physical path. In particular, no `src/platform` target is established.

| Business/technical concern | Current owner(s) evidenced in code | Status | Proposed canonical owner / migration note |
|---|---|---|---|
| Identity and user context | `domain/identity.py`, `services/authentication.py`, API dependency wiring | TRANSITIONAL | Domain identity types + application authentication use case/port; preserve token/current-user behavior. |
| Authorization / RBAC | `domain/authorization.py`, `services/authorization.py`, `repositories/rbac.py` | TRANSITIONAL | Application authorization policy/use case using an application port; SQL adapter in repositories/infrastructure. |
| Organization / quotas | `domain/organization.py`, `domain/quota.py`, `services/quota.py`, organization/quota repositories | TRANSITIONAL | Domain rules + application quota use case + repository port/adapter. |
| Dataset/workspace/project | `domain/studio/*`, `application/workspace`, `application/datasets`, corresponding repositories and `database/models.py` | ACTIVE, mixed | Domain owns entities; application owns ingestion/scoping; persistence owns rows/adapters; upload/storage adapters in infrastructure. |
| Data quality and reports | `domain/quality`, `application/quality`, `services/validation_service.py`, `services/data_operations.py`, agents, capabilities, validators | TRANSITIONAL | Application quality use case orchestrates canonical capability execution; primitives/rules and report adapter retain current formulas/output contracts. Characterize current `QualityService` and legacy validation semantics before merging. |
| Capability catalog/dependencies | `domain/capability*`, `domain/dependency_resolver.py`, agents and tests | ACTIVE | Domain owns metadata/selection rules; application planning coordinates use; registry/execution owns dispatch. |
| Capability implementation/execution | `capabilities/`, `execution/capabilities/`, container | ACTIVE, mixed | `capabilities/` owns implementations; `execution/` owns lifecycle/dispatch/traces; domain owns contracts. Replace direct `services.data_operations` dependency with application port/use case. |
| Intent, requirements, planning | `agents/intent_classifier.py`, `agents/requirement.py`, `agents/planner.py`, `domain/intent_resolver.py`, `domain/plans.py`, `application/workflows` and Copilot | ACTIVE, mixed | Domain owns typed intent/plan contracts and deterministic rules; application use cases coordinate; agents are optional adapters/collaborators behind explicit ports. |
| Workflow authoring/runtime/history | `application/workflows/*`, `execution/workflow/engine.py`, `domain/studio/workflow.py`, `domain/studio/runtime.py`, queue adapters, workflow repositories | ACTIVE | One use-case runtime invoking one execution engine/worker pipeline. Keep queue backend as delivery adapter; map existing inline and queued state transitions before alteration. |
| Execution context/plans/traces | `domain/execution*`, `execution/context`, `execution/planning`, `execution/tracing`, infrastructure/repository trace storage | ACTIVE | Domain owns context/status/trace values; execution coordinates; trace ports in application or execution contracts, SQL adapter in persistence. |
| Approval, risk, changesets, rollback | `domain/{approval,risk,changeset}.py`, application packages, repositories and infrastructure persistence | ACTIVE | Existing `application/approval`, `risk`, `changesets` are likely canonical use-case owners; preserve approval gates, signatures, snapshots, rollback and audit atomicity. |
| Audit and compliance | domain audit/compliance; application audit; `services/compliance.py`; audit/policy repositories | TRANSITIONAL | Domain policies/records + application audit/compliance use cases + persistence ports; telemetry should not own business audit semantics. |
| Lineage | `domain/lineage.py`, `application/lineage`, lineage repository and API route | ACTIVE | Application lineage use case and persistence adapter; preserve event schema and API visibility. |
| Channel sync / credentials | `domain/channel_sync.py`, application channels, infrastructure connectors/http/security, repositories and route modules | TRANSITIONAL | Domain sync values/policies; application sync use cases/ports; infrastructure channel connector and credential adapter; repositories must not depend on application. |
| Marketplace | `domain/marketplace.py`, application marketplace/ports, infrastructure marketplace, marketplace repository/API | ACTIVE | Good existing separation candidate; inspect signature/archive/install lifecycle before moving any responsibility. |
| Rules / retrieval | `rule_engine/`, `repositories/rules.py`, `infrastructure/rules`, `agents/rule_retriever.py`, application rules, Chroma | ACTIVE, mixed | Domain rule contracts; application rule use case; infrastructure retriever/index adapter; YAML parser/evaluator has explicit boundary. Preserve existing rule-pack formats and Chroma behavior. |
| Plugins / validators | `plugins/`, `validators/`, `plugins.registry`, capability validation | TRANSITIONAL | `plugins` is the extension contract/registry; migrate legacy validator implementations one at a time, preserving discovery order and fallback until callers are proven migrated. |
| AI / copilot / memory | `agents/llm.py`, `application/copilot`, `application/memory`, `ai/*`, domain memory, repository memory, Chroma/Google dependencies | TRANSITIONAL, partly unverified | Application owns copilot/memory use cases; domain owns persisted memory concepts; provider/vector stores are infrastructure adapters. Inventory `ai/` call sites before assigning it; tests reference much of the `agents/` API. Keep model output non-authoritative for permissions/execution. |
| HTTP schemas | `schemas/requests.py`, `schemas/responses.py`, `schemas/copilot.py`, `schemas/marketplace.py`, `api/schemas.py`, `api/routes/*` | TRANSITIONAL | Public transport contracts in `api` (or a clearly owned interface schema package); domain types stay framework/API-independent. Avoid breakage to OpenAPI routes/response shapes. |
| SQLAlchemy schema/session | `database/models.py`, `database/migrations/`, `database/migrations/env.py`, `database.models.make_session_factory` | ACTIVE, mixed | `database` / `infrastructure.persistence` owns records, sessions and Alembic. Remove startup schema creation only after test/bootstrap and deployment paths are explicit. |
| Repositories | `repositories/*.py` (23 files) and nested `models/repositories` | ACTIVE, transitional | One persistence adapter implementation per aggregate; define contracts at application boundary. Nested `models/repositories` requires import/test reference audit; do not assume duplicate implementation from name alone. |
| Reports / artifacts / upload | `reports/`, `views/reports`, infrastructure upload/storage, application materializer, routes | ACTIVE, mixed | Application owns artifact use cases/metadata; infrastructure owns storage/upload; report rendering is adapter. Verify artifact IDs/root containment, formula escaping, size limits and retention. |
| Configuration/observability/ops | `configs/`, infrastructure telemetry/logging, Docker/Nginx/worker | ACTIVE | Settings and process composition at outer boundary; infrastructure owns adapters. Production deployment/alerting validation remains external per handoff. |
| Legacy service package | `services/` includes container plus data/security/governance behavior | TRANSITIONAL | Decompose behavior into application use cases and infrastructure composition; keep a documented, tested composition shim until import/call-site census is empty. |
| Legacy controllers/views/models | `controllers/`, `views/`, `models/`, root scripts | COMPATIBILITY or UNVERIFIED | Verify imports, runtime launch commands and user docs. Keep tested aliases/entrypoints until downstream usage is established; then use deprecation period before deletion. |

## Ownership decisions requiring characterization (not user clarification yet)

The current code/tests can answer these through targeted tracing before implementation: whether `QualityService` or `DataOperationsService` is the canonical output/validation path per endpoint; which synchronous versus queued workflow paths are externally used; what `ai/` modules are imported in runtime; whether report/view modules are active; and whether `models/*` nested packages expose more than the documented aliases. These are migration discovery tasks, not justification to stop the current read-only phase.

## Post-slice ownership delta (2026-10-02)

- **Memory persistence:** the application-owned contract is `application.memory.ports.AgentMemoryPersistencePort`; SQL behavior is owned by `infrastructure.persistence.agent_memory_repository`; `repositories.agent_memory` is retained as compatibility facade.
- **Channel sync jobs:** `application.channels.ChannelSyncService` owns sync-job use-case behavior, `domain.channel_sync` owns types/state, and the repository owns persistence. The status read now follows this application service. The separate channel-list query has no established application owner yet.
- No other ownership claim in this snapshot is resolved by the two slices. Quality/validation, authorization/compliance/quota, and workflow/runtime ownership remain split as previously described.

See `POST_SLICE_ARCHITECTURE_REVIEW.md` for all requested concepts, remaining compatibility paths, and evidence-bounded uncertainty.
