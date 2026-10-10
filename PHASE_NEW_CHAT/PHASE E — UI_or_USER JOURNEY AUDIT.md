PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Product Architect + UX Auditor + Technical Product Auditor.

READ-ONLY ONLY.
DO NOT MODIFY UI OR BACKEND.

==================================================
MASTER CONTEXT
==================================================

PROJECT: Autonomous E-commerce Data Operations Platform

ROLE:
Bạn là Senior Software Architect + Repository Auditor + Product/UX Auditor.
Nhiệm vụ là audit, phân tích và lập kế hoạch dựa trên evidence thực tế của repository.

QUAN TRỌNG:
Đây là dự án EXISTING. Không được mặc định kiến trúc hiện tại là hoàn hảo, nhưng cũng không được mặc định code cũ là dead code.

NGUYÊN TẮC BẮT BUỘC:
1. Audit trước, modification sau.
2. Không tự ý sửa repository.
3. Không delete file/code.
4. Không move/rename module.
5. Không refactor.
6. Không thay đổi DB/schema/migration.
7. Không thay đổi Docker/Compose.
8. Không thay đổi requirements/dependencies.
9. Không thay đổi config/env/API/routes.
10. Không thay đổi behavior/UI.
11. Nếu cần modification, chỉ ĐỀ XUẤT, không thực hiện.
12. Không coi "không có direct import" là bằng chứng file dead.
13. Phải xét:
   - static imports
   - dynamic imports
   - dependency injection
   - runtime registration
   - entrypoints
   - API routes
   - worker
   - dashboard/Streamlit
   - plugins
   - filesystem references
   - templates
   - tests
   - Docker/Compose
   - CI/CD
   - Alembic
   - config/env
   - reflection/string references
   - external-consumer possibility
14. Không gửi nội dung .env hoặc secret.
15. Nếu evidence không đủ: ghi UNKNOWN.
16. Không biến inference thành fact.
17. Phân biệt rõ:
   DEAD
   LEGACY_ACTIVE
   COMPATIBILITY
   HISTORICAL
   DUPLICATED
   CURRENT
   UNKNOWN
18. "Legacy" không đồng nghĩa "dead".
19. "Old" không đồng nghĩa "unused".
20. Test pass không đồng nghĩa production-ready.
21. Không được xóa code chỉ để làm kiến trúc đẹp hơn.

CURRENT KNOWN BASELINE:

ARCHITECTURE_STATUS:
HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CODE_CLEANUP_STATUS:
NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

FILE_CLEANUP_STATUS:
GENERATED_ARTIFACT_CANDIDATES_IDENTIFIED; PERSISTENT DATA PROTECTED

UI_STATUS:
PARTIALLY_EVIDENCED

USER_FLOW_STATUS:
NOT_YET_FULLY_AUDITED

CAPABILITY_STATUS:
NOT_YET_FULLY_AUDITED

COMMERCIAL_READINESS:
PARTIALLY_EVIDENCED

PRODUCTION_READINESS:
PARTIAL / NOT_ESTABLISHED

SAFE_TO_DELETE_NOW:
NONE

REQUIRES_MORE_EVIDENCE:
ai/
controllers/
views/
data_quality.db
chroma/
compatibility re-exports

REQUIRES_RUNTIME_VERIFICATION:
production Compose startup
worker deployment/recovery
effective DATABASE_URL
Alembic vs create_all behavior
Chroma exposure/configuration
actual Streamlit user journey
plugin runtime loading

REQUIRES_EXPLICIT_AUTHORIZATION:
Any deletion/move/rename
Any DB/schema change
Any migration change
Any dependency/config/Docker change
Any compatibility-shim removal

KNOWN ENTRYPOINTS:
- app.main = current API application entrypoint candidate
- main.py = backward-compatible wrapper
- app.dashboard = current Streamlit dashboard
- dashboard.py = backward-compatible wrapper
- worker.py = current Redis workflow worker entrypoint

KNOWN ARCHITECTURE EVIDENCE:
- FastAPI runtime exists.
- 15 API routers are registered.
- Streamlit dashboard exists.
- Redis-backed workflow execution consumer exists.
- services/container.py is a major composition root.
- application/domain/repositories/infrastructure/execution/agents/capabilities are actively referenced.
- application <-> services has bidirectional dependencies.
- rule_engine is actively referenced.
- validators is actively referenced.
- plugins have dynamic import behavior.
- controllers/ has no proven internal runtime consumer.
- ai/ has no proven direct imports.
- views/ appears to be an empty/scaffold area.
- controllers/ai/views must NOT be deleted without additional evidence.
- data_quality.db and chroma state must be treated as potentially persistent.
- Docker/Compose and CI/CD exist.
- production deployment evidence is incomplete.

KNOWN ENVIRONMENT:
- Windows 11
- PowerShell 5.1
- Python 3.13.15
- Git 2.55
- Node 24.18
- npm 11.16
- active venv

KNOWN GIT:
- branch: main
- working tree was clean at last audit

KNOWN TEST BASELINE:
- 994 passed
- 0 failed
- 0 errors
- 0 skipped
- 0 warnings

IMPORTANT:
The 994 passing tests prove regression coverage at the tested level only.
They do NOT prove production readiness, UX completeness, commercial readiness, deployment correctness, security isolation, or that all legacy code is unused.

WORKING STYLE:
- Evidence-first.
- Read-only.
- Precise.
- Vietnamese response.
- Use tables where useful.
- Mark confidence/evidence level.
- Do not invent missing information.
- Do not repeat already-established facts unless needed.
- At the end clearly state:
  PROVEN
  PARTIALLY_EVIDENCED
  UNKNOWN
  BLOCKED
  NEXT ACTION

==================================================
LATEST CONSOLIDATED STATE
==================================================

ARCHITECTURE_STATUS = HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CODE_CLEANUP_STATUS = NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

FILE_CLEANUP_STATUS = GENERATED_ARTIFACT_CANDIDATES_IDENTIFIED; PERSISTENT_DATA_PROTECTED

UI_STATUS = PARTIALLY_EVIDENCED

USER_FLOW_STATUS = NOT_YET_FULLY_AUDITED

CAPABILITY_STATUS = NOT_YET_FULLY_AUDITED

COMMERCIAL_READINESS = PARTIALLY_EVIDENCED

PRODUCTION_READINESS = PARTIAL / NOT_ESTABLISHED

DEAD_CONFIRMED = NONE

SAFE_TO_DELETE_NOW = NONE

SAFE_TO_CONSOLIDATE_NOW = NONE

PHASE_D_ARCHITECTURE_STATUS = AUDIT_COMPLETE; INCREMENTAL_CONVERGENCE_RECOMMENDED

PHASE_D_DEPENDENCY_STATUS = STATIC_IMPORT_DIRECTION_PROVEN_CLEAN_AT_CORE_BOUNDARIES

PHASE_D_DOMAIN_STATUS = CLEAN; NO_OUTBOUND_LAYER_DEPENDENCY_PROVEN

PHASE_D_EXECUTION_STATUS = CENTRALIZED; CAPABILITY_EXECUTION_SERVICE_CONFIRMED_AS_ACTIVE_EXECUTION_BOUNDARY

PHASE_D_AGENTS_STATUS = CLEAN_AT_IMPORT_LEVEL; NO_APPLICATION/SERVICES/EXECUTION/PERSISTENCE/INFRASTRUCTURE_DEPENDENCY_PROVEN

PHASE_D_APPLICATION_STATUS = ACTIVE_APPLICATION_LAYER_WITH_JUSTIFIED_CROSS_CUTTING_SERVICE_COUPLING

PHASE_D_SERVICES_STATUS = MIXED_PACKAGE; CROSS_CUTTING + RUNTIME/TRANSITIONAL SERVICES + COMPOSITION_ROOT

PHASE_D_REPOSITORIES_STATUS = MIXED_CANONICAL_AND_COMPATIBILITY; MIGRATION_MUST_BE_CONCERN_BY_CONCERN

PHASE_D_COMPATIBILITY_STATUS = ai_CONTROLLERS_VIEWS_AND_SELECTED_REPOSITORY_SURFACES_REMAIN_UNVERIFIED/COMPATIBILITY_LAYERS

PHASE_D_COMPOSITION_ROOT_STATUS = services.container IS ACTIVE COMPOSITION ROOT AND MUST BE PRESERVED

PHASE_D_ARCHITECTURAL_REWRITE = NOT_JUSTIFIED

PHASE_D_BIG_BANG_CLEANUP = NOT_JUSTIFIED

PHASE_D_RUNTIME_VERIFICATION_REQUIRED =
  production_compose_startup;
  worker_deployment_and_recovery;
  effective_DATABASE_URL;
  Alembic_vs_create_all_behavior;
  Chroma_runtime_exposure/configuration;
  actual_Streamlit_user_journey;
  plugin_runtime_loading;
  effective_production_configuration;
  Copilot_production_path

PHASE_D_CLEANUP_CANDIDATES =
  P1: unused PlannerAgent/RequirementAgent imports in api/routes/copilot.py;
  P2: legacy repositories/approval.py compatibility implementation;
  P3: services.DataOperationsService boundary convergence;
  P4: api/routes/risk.py independent build_container() composition inconsistency

PHASE_D_MUST_PRESERVE =
  domain boundary;
  execution boundary;
  active agents/Copilot path;
  services.container composition root;
  persistent DB/schema/migrations;
  Chroma data;
  artifacts/reports persistent data;
  compatibility/unverified ai/controllers/views surfaces;
  active repositories until consumer evidence exists

PHASE_D_EXTERNAL_CONSUMER_RISK = UNKNOWN

PHASE_D_TARGET_ARCHITECTURE =
  API/UI
      ->
  APPLICATION / USE-CASE ORCHESTRATION
      ->
  DOMAIN
      ^
      |
  CROSS-CUTTING POLICIES / PORTS

  APPLICATION / USE-CASE ORCHESTRATION
      ->
  AGENTS (reasoning / provider-facing abstractions where required)
      ->
  EXECUTION (workflow/runtime/capability execution)
      ->
  CAPABILITY REGISTRY / DOMAIN CAPABILITIES

  APPLICATION / USE-CASE ORCHESTRATION
      ->
  INFRASTRUCTURE / REPOSITORIES / QUEUE / STORAGE / EXTERNAL ADAPTERS

  services.container
      =
  composition root / dependency wiring

  Transitional services and compatibility repositories should converge
  incrementally toward explicit application ports/adapters only when
  runtime and external-consumer evidence permits.

PHASE_D_MIGRATION_ORDER =
  1. Preserve current runtime and establish production/runtime evidence.
  2. Perform low-risk local cleanup only where references are proven internal.
  3. Establish consumer/deprecation evidence before compatibility removal.
  4. Converge DataOperationsService boundary.
  5. Normalize composition/DI inconsistency in risk route.
  6. Migrate remaining repository concerns individually.
  7. Re-audit architecture after each bounded migration slice.
  8. Only then evaluate compatibility-surface retirement.

PHASE_E_PRECONDITIONS =
  Phase D architecture baseline accepted;
  no source deletion authorized implicitly;
  runtime/product behavior treated as protected;
  UI/user journey and capability coverage remain outstanding.

==================================================
PHASE D HANDOFF
==================================================

FROM:
  PHASE D — ARCHITECTURE CLEANUP / ARCHITECTURE AUDIT

STATUS:
  COMPLETE FOR STATIC ARCHITECTURE AUDIT

HANDOFF_TO:
  PHASE E — UI / USER JOURNEY / CAPABILITY COVERAGE AUDIT

CORE_CONCLUSION:
  The repository does not justify a broad architectural rewrite.
  The architecture is hybrid, with an active application layer,
  clean core domain/execution/agent boundaries, a mixed services package,
  mixed canonical/compatibility repository surfaces, and several
  transitional compatibility layers.

PROVEN:
  - API composition root is active.
  - Worker composition root is active.
  - services.container is the central dependency composition root.
  - Domain has no proven outbound dependency on outer layers.
  - Execution is a distinct active runtime boundary.
  - CapabilityExecutionService is the central execution substrate.
  - Agents do not statically depend on application/services/execution/
    persistence/infrastructure.
  - Application -> services coupling is primarily cross-cutting policy usage.
  - Copilot API path is API -> CopilotService; route bypass is disproven.
  - CopilotService -> PlannerAgent/RequirementAgent and CopilotAgent
    responsibilities are intentional and non-duplicate.
  - DataOperationsService is active and transitional, not dead.
  - ValidationService is active runtime support, not duplicate.
  - services.container is not a cleanup target.
  - controllers/, views/, and ai/ are empty/unreferenced internally,
    but external usage remains unknown.
  - repositories/ is mixed active persistence + compatibility; it is not
    safe to treat the whole package as legacy.
  - repositories/approval.py is the strongest legacy deletion candidate,
    but external-consumer uncertainty blocks deletion.
  - persistent database/schema/migrations/Chroma/artifacts remain protected.

NOT_PROVEN:
  - No source file is DEAD_CONFIRMED.
  - No broad package is safe to delete.
  - No compatibility surface is safe to remove.
  - No production runtime topology has been fully verified.
  - No complete UI/user journey has been audited.
  - No complete capability/product coverage audit has been performed.
  - External consumers of compatibility paths are unknown.

ARCHITECTURAL_DEBT:
  1. Transitional application -> services coupling.
  2. DataOperationsService remains outside the application package.
  3. Mixed repository architecture with compatibility implementations.
  4. api/routes/risk.py has a local composition/DI inconsistency.
  5. AutonomousOperationsOrchestrator has high orchestration responsibility
     concentration; God-object classification remains unproven.
  6. PlannerAgent / PlanValidator have some conceptual overlap, but are
     not currently proven duplicates.
  7. Plugin architecture retains validators fallback/compatibility paths.
  8. Production runtime/configuration evidence remains incomplete.
  9. Compatibility surfaces have unresolved external-consumer uncertainty.

SAFE_ACTIONS:
  - Documentation/audit updates.
  - Evidence gathering.
  - Runtime verification planning.
  - Low-risk cleanup planning for proven-unused local imports.
  - Bounded migration planning.

NOT_AUTHORIZED_BY_THIS_AUDIT:
  - Delete/move/rename source files.
  - Delete compatibility packages.
  - Remove repositories/approval.py.
  - Modify DB/schema/migrations.
  - Change dependencies/config/Docker/Compose.
  - Refactor application/services boundaries.
  - Replace composition root.
  - Remove ai/controllers/views.
  - Alter persistent data.

PHASE E OBJECTIVE:
  Determine whether the current product surface actually delivers the
  intended user workflows and capabilities, with emphasis on:
  - Streamlit dashboard user journey.
  - API-to-UI feature reachability.
  - Dataset ingestion/profile/quality flows.
  - Workflow authoring/simulation/execution flows.
  - Approval/change-set/governance flows.
  - Risk/compliance/quota behavior as user-visible capabilities.
  - Copilot workflow authoring and interactive tool flow.
  - Marketplace/channel flows.
  - Lineage/audit observability.
  - Error/loading/empty-state behavior.
  - Capability registry coverage versus exposed product actions.
  - Gaps between backend capability and actual user-facing access.

PHASE E GUARDRAILS:
  - Read-only audit.
  - No source modifications.
  - No deletion.
  - No refactor.
  - No schema/migration/config/dependency/Docker changes.
  - Do not infer missing UI functionality solely from backend code.
  - Distinguish backend capability from reachable user journey.
  - Mark each finding PROVEN / PARTIALLY_EVIDENCED / UNKNOWN / BLOCKED.
  - Preserve all compatibility and persistent-data surfaces until separately
    authorized and evidenced.

PHASE E STARTING HYPOTHESIS:
  Backend architecture is materially more mature than the currently proven
  user-facing/runtime surface. The next audit should therefore establish
  actual user journeys and capability reachability before any cleanup work
  is approved.

NEXT_PHASE:
  PHASE E — UI / USER JOURNEY / CAPABILITY COVERAGE AUDIT

==================================================
PHASE
==================================================

PHASE E — ACTUAL UI / USER JOURNEY AUDIT

OBJECTIVE:
Determine what a real user can actually accomplish through the current product UI, not merely what exists in backend code.

==================================================
KNOWN UI
==================================================

- app/dashboard.py = current Streamlit dashboard candidate
- dashboard.py = compatibility launcher
- app/api_client.py exists
- FastAPI backend exists

Do not assume backend capability is user-accessible.

==================================================
USER JOURNEY
==================================================

Audit:

1. Entry
2. Authentication
3. Authorization
4. Organization
5. Workspace
6. Project
7. Dataset
8. Data upload/import
9. Mapping
10. Validation
11. Rules
12. Sync
13. Workflow authoring
14. Workflow execution
15. Queue/execution status
16. Quality results
17. Reports
18. Changesets
19. Approval
20. Risk
21. Audit
22. Lineage
23. Semantic search
24. AI/Copilot
25. Monitoring
26. Configuration
27. Integrations
28. Export

==================================================
FOR EVERY CAPABILITY
==================================================

Determine:

BACKEND =
API =
UI =
UI_ROUTE_OR_CONTROL =
TESTS =
DOCUMENTATION =
DISCOVERABLE =
USER_CAN_COMPLETE =
ERROR_STATE =
LOADING_STATE =
EMPTY_STATE =
PERMISSION_BEHAVIOR =
TENANT_CONTEXT =
RESULT_VISIBILITY =
RECOVERY_PATH =

STATUS:

PROVEN
PARTIALLY_EVIDENCED
UNKNOWN
BLOCKED
NOT_APPLICABLE

==================================================
OUTPUT
==================================================

1. ACTUAL USER JOURNEY

2. SCREEN / PAGE MAP

3. CAPABILITY MATRIX

Columns:

CAPABILITY
BACKEND
API
UI
TESTS
DOCUMENTATION
USER_ACCESSIBLE
STATUS

Minimum capabilities:

authentication
authorization
organizations
workspaces
projects
datasets
channels
mappings
sync
workflow
queued execution
validation
rules
semantic search
AI/Copilot
changesets
approvals
risk
audit
lineage
reports
exports
monitoring
configuration
integrations

4. USER JOURNEY GAPS

5. UI GAPS

6. BACKEND-ONLY CAPABILITIES

7. PARTIAL CAPABILITIES

8. BLOCKED JOURNEYS

9. MUST_FIX_BEFORE_FIRST_CUSTOMER

10. SHOULD_FIX_BEFORE_PAID_SCALE

11. NICE_TO_HAVE

12. UNKNOWN

13. FINDINGS THAT AFFECT PHASE F

==================================================
STATE CONSISTENCY
==================================================

Compare against previous consolidated state and Phase D.

If new evidence contradicts prior findings:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Do not silently overwrite previous state.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = E
PHASE_NAME = UI_AND_USER_JOURNEY
PHASE_STATUS =

UI_STATUS =
USER_FLOW_STATUS =
CAPABILITY_STATUS =

SAFE_TO_MODIFY_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

PROVEN =
PARTIALLY_EVIDENCED =
UNKNOWN =
BLOCKED =

B. PHASE HANDOFF

OBJECTIVE =
SCOPE_AUDITED =

PROVEN =
PARTIALLY_EVIDENCED =
UNKNOWN =
BLOCKED =

ACTUAL_USER_JOURNEY =
UI_SURFACES =
BACKEND_ONLY_CAPABILITIES =
PARTIAL_CAPABILITIES =
BLOCKED_JOURNEYS =

MUST_FIX_BEFORE_FIRST_CUSTOMER =
SHOULD_FIX_BEFORE_PAID_SCALE =
NICE_TO_HAVE =

DO_NOT_TOUCH =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

KEY_FINDINGS =
AFFECTED_FILES =
AFFECTED_MODULES =
RISKS_DISCOVERED =
OPEN_QUESTIONS =

NEW_EVIDENCE_REQUIRED_FOR_NEXT_PHASE =
INPUT_REQUIRED_BY_NEXT_PHASE =
RECOMMENDED_NEXT_ACTION =

STATE_CHANGE =

C. UPDATED CONSOLIDATED PROJECT STATE

Create self-contained state for Phase F.

Preserve all previous findings.

Update:

UI_STATUS =
USER_FLOW_STATUS =
CAPABILITY_STATUS =

CURRENT_USER_JOURNEY =
CURRENT_UI_SURFACES =
BACKEND_ONLY_CAPABILITIES =
USER_ACCESSIBLE_CAPABILITIES =
BLOCKED_CAPABILITIES =

MUST_FIX_BEFORE_FIRST_CUSTOMER =
SHOULD_FIX_BEFORE_PAID_SCALE =
NICE_TO_HAVE =

Also preserve architecture, cleanup, runtime, security and commercial unknowns.