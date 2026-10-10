PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Software Architect.

READ-ONLY ONLY.
DO NOT REFACTOR.
DO NOT MODIFY ARCHITECTURE.

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

ARCHITECTURE_STATUS =
    HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CODE_CLEANUP_STATUS =
    NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

FILE_CLEANUP_STATUS =
    GENERATED_ARTIFACT_CANDIDATES_IDENTIFIED;
    PERSISTENT_DATA_PROTECTED

UI_STATUS =
    PARTIALLY_EVIDENCED

USER_FLOW_STATUS =
    NOT_YET_FULLY_AUDITED

CAPABILITY_STATUS =
    NOT_YET_FULLY_AUDITED

COMMERCIAL_READINESS =
    PARTIALLY_EVIDENCED

PRODUCTION_READINESS =
    PARTIAL / NOT_ESTABLISHED

SAFE_TO_DELETE_NOW =
    NONE

SAFE_TO_CONSOLIDATE_NOW =
    NONE

--------------------------------------------------
CURRENT
--------------------------------------------------

- FastAPI application exists and is active.
- Streamlit dashboard exists and is active.
- Redis-backed workflow worker exists.
- Application/domain/repository/infrastructure/execution/agents/capabilities
  are active architectural areas.
- services.container is a composition root, not a business-service duplicate.
- CapabilityRegistry is the canonical runtime capability registry.
- CapabilityExecutor is the capability step execution mechanism.
- CapabilityExecutionService is the application execution boundary around
  validation, tracing, telemetry, lineage, and CapabilityExecutor.
- PlannerAgent creates deterministic ExecutionPlan objects.
- PlanValidator validates execution plans at the runtime/pre-execution boundary.
- WorkflowEngine manages persisted workflow execution lifecycle.
- CopilotAgent is the provider-facing LLM boundary.
- CopilotService is the application orchestration boundary for Copilot.
- CopilotToolRegistry is an allowlisted typed tool registry.
- CopilotApplicationTools are application-facing adapters/delegators.
- AutonomousOpsService is the autonomous-operation policy gate.
- AutonomousOperationsOrchestrator coordinates the bounded
  Detect → Diagnose → Plan → Simulate → Govern → ChangeSet →
  Approval → Apply → Verify → Learn lifecycle.
- Rule engine is active.
- BusinessRuleValidation is the current rule-validation implementation.
- RuleValidator is an active backward-compatible facade.
- Validators remain active.
- Dynamic plugin loading exists.
- API compatibility surfaces and backward-compatible entrypoints exist.

--------------------------------------------------
KNOWN_DUPLICATION
--------------------------------------------------

CONFIRMED:

1. repositories/approval.py::ApprovalRepository
   ↔ infrastructure/persistence/approval_repository.py::ApprovalRepository

   Status:
   - DUPLICATED
   - FUNCTIONALLY_SUPERSEDED
   - ACTIVE_REPLACEMENT_CONFIRMED
   - LEGACY_ACTIVE
   - NO_INTERNAL_PRODUCTION_CONSUMER_PROVEN
   - EXTERNAL_USAGE_UNKNOWN

2. repositories/approval.py::RiskPolicyRepository
   ↔ infrastructure/persistence/risk_repository.py::RiskRepository

   Status:
   - LEGACY_CANDIDATE
   - FUNCTIONALLY_SUPERSEDED
   - ACTIVE_REPLACEMENT_CONFIRMED
   - NO_PRODUCTION_CONSUMER_PROVEN
   - EXTERNAL_USAGE_UNKNOWN
   - PERSISTENT_SCHEMA_STILL_ACTIVE

No additional duplication is sufficiently proven to authorize
consolidation or deletion.

--------------------------------------------------
KNOWN_RESPONSIBILITY_OVERLAP
--------------------------------------------------

1. PlannerAgent ↔ PlanValidator

   - Both perform contract/type/input/output-related validation.
   - Planner creates an ExecutionPlan.
   - PlanValidator validates a plan at the runtime/pre-execution boundary.
   - Overlap is architectural/lifecycle-based.
   - DUPLICATION NOT PROVEN.
   - NOT SAFE TO CONSOLIDATE.

2. services.validation_service ↔ validators/* ↔ rule_engine

   - validation_service orchestrates validation execution.
   - validators contain validation implementations.
   - rule_engine contains declarative business-rule evaluation.
   - SAME RESPONSIBILITY DUPLICATION NOT PROVEN.

3. AutonomousOperationsOrchestrator ↔ multiple application services

   - Orchestrator has high responsibility concentration.
   - It delegates to existing services rather than reimplementing their
     core logic.
   - This is architectural concentration/debt, not proven duplication.

4. application ↔ services.authorization/compliance/quota

   - Boundary coupling exists.
   - No safe consolidation established.

--------------------------------------------------
KNOWN_TRANSITIONAL_LAYERS
--------------------------------------------------

- repositories/approval.py legacy persistence implementation.
- legacy RiskPolicyRepository.
- backward-compatible entrypoint wrappers.
- RuleValidator compatibility facade.
- API/schema compatibility re-exports.
- domain memory compatibility re-export.
- Other compatibility surfaces whose external usage remains UNKNOWN.

--------------------------------------------------
KNOWN_COMPATIBILITY_LAYERS
--------------------------------------------------

- api/schemas.py
- domain/memory.py
- RuleValidator
- main.py
- dashboard.py
- package/export compatibility surfaces

These must NOT be classified as dead merely because direct internal
imports are limited or absent.

--------------------------------------------------
KNOWN_ARCHITECTURAL_DEBT
--------------------------------------------------

- AutonomousOperationsOrchestrator has high responsibility concentration.
- PlannerAgent and PlanValidator contain some overlapping validation checks.
- RuleValidator has ambiguous behavior when passed a non-RuleSet mapping
  and may return [].
- Application ↔ services coupling exists in governance-related areas.
- External consumers outside the repository cannot be ruled out.
- Production runtime topology has not been fully verified.
- Plugin runtime loading has not been fully verified end-to-end.
- Effective production configuration has not been fully verified.
- Copilot production execution journey has not been fully verified.

--------------------------------------------------
LEGACY_OR_INVESTIGATION
--------------------------------------------------

- repositories/approval.py
- legacy RiskPolicyRepository
- controllers/
- ai/
- views/
- compatibility surfaces with unresolved external-consumer status

--------------------------------------------------
HISTORICAL
--------------------------------------------------

- database/migrations/archive/legacy_versions
- other explicitly historical migration artifacts already identified

Historical migration artifacts are not dead code and persistent schema/data
must remain protected.

--------------------------------------------------
DEAD_CONFIRMED
--------------------------------------------------

NONE FROM PHASE C.

Previously identified deletion candidate remains:
- repositories/approval.py

But deletion is BLOCKED by authorization.

--------------------------------------------------
PROTECTED_DATA
--------------------------------------------------

- approvals table
- risk_policies table
- ApprovalRecord
- RiskPolicyRecord
- canonical migrations
- persistent database data
- Chroma persistent data until lifecycle/configuration is verified

Legacy repository implementation being obsolete does NOT imply that the
underlying persistent schema or data is obsolete.

--------------------------------------------------
UNKNOWN
--------------------------------------------------

- External consumers outside repository.
- Complete plugin runtime loading behavior.
- Effective production DATABASE_URL/configuration.
- Production worker deployment/recovery semantics.
- Complete Streamlit user journey.
- Complete Copilot production execution path.
- Complete risk-policy semantic convergence between legacy/current repositories.
- Runtime behavior of unresolved controllers/ai/views surfaces.
- Full commercial-readiness evidence.

--------------------------------------------------
BLOCKED
--------------------------------------------------

The following remain blocked:

- deleting repositories/approval.py
- deleting legacy RiskPolicyRepository
- deleting/moving/renaming source files without authorization
- schema/database changes
- migration changes
- dependency changes
- Docker/configuration changes
- compatibility-shim removal
- any cleanup requiring external-consumer assumptions

--------------------------------------------------
SAFETY GATES
--------------------------------------------------

NO SOURCE DELETE IS APPROVED BY PHASE C.

NO CONSOLIDATION IS APPROVED BY PHASE C.

Persistent data/schema remains protected.

External-consumer uncertainty remains a deletion blocker.

Read-only evidence gathering remains the permitted audit mode unless
explicit authorization is supplied.

==================================================
PHASE C HANDOFF
==================================================

PHASE_ID =
    C

PHASE_NAME =
    DUPLICATION_AUDIT

STATUS =
    COMPLETE

--------------------------------------------------
PHASE C VERDICT
--------------------------------------------------

DUPLICATION_STATUS =
    LIMITED;
    MOSTLY_LAYERED;
    TWO LEGACY PERSISTENCE DUPLICATIONS CONFIRMED

SAFE_TO_CONSOLIDATE_NOW =
    NONE

SAFE_TO_DELETE_NOW =
    NONE

PRIMARY_CONFIRMED_DUPLICATIONS =
    - repositories/approval.py::ApprovalRepository
      ↔ infrastructure.persistence.ApprovalRepository
    - repositories/approval.py::RiskPolicyRepository
      ↔ infrastructure.persistence.RiskRepository

--------------------------------------------------
IMPORTANT NON-DUPLICATIONS
--------------------------------------------------

Do NOT consolidate solely because of naming or overlapping-looking
responsibilities:

- PlannerAgent + PlanValidator
- CapabilityExecutionService + CapabilityExecutor
- CopilotToolRegistry + CapabilityRegistry
- CopilotService + CopilotAgent
- WorkflowEngine + CapabilityExecutionService
- AutonomousOpsService + AutonomousOperationsOrchestrator
- services.container + application services
- RuleValidator + BusinessRuleValidation

These have distinct lifecycle, boundary, orchestration, compatibility,
or runtime responsibilities based on the evidence gathered.

--------------------------------------------------
PHASE D INSTRUCTIONS
--------------------------------------------------

1. Remain evidence-first and READ-ONLY unless explicit authorization is
   provided.

2. Do not delete repositories/approval.py automatically.

3. Treat repositories/approval.py as the strongest deletion candidate,
   but keep it BLOCKED until explicit authorization is given.

4. Do not delete or modify:
   - persistent models
   - approvals
   - risk_policies
   - migrations
   - Chroma data
   - compatibility surfaces

5. Continue investigation of:
   - ai/
   - controllers/
   - views/
   - dynamic plugin loading
   - external-consumer uncertainty
   - production runtime topology
   - worker deployment/recovery
   - effective DATABASE_URL/configuration
   - Copilot end-to-end execution
   - Streamlit actual user journey

6. Do not infer DEAD from:
   - zero direct imports
   - zero package imports
   - zero composition-root imports
   - absence from obvious API routes

7. Continue checking:
   - static imports
   - dynamic imports
   - DI/container wiring
   - runtime registration
   - entrypoints
   - API routes
   - worker
   - dashboard
   - plugins
   - filesystem/templates
   - tests
   - Docker/Compose
   - CI/CD
   - migrations
   - reflection/string references
   - external-consumer possibility

8. Preserve the distinction:
   CURRENT
   LEGACY_ACTIVE
   COMPATIBILITY
   HISTORICAL
   DUPLICATED
   DEAD
   UNKNOWN
   BLOCKED

--------------------------------------------------
PHASE D SAFETY GATE
--------------------------------------------------

Before any deletion candidate is approved, require evidence for:

- internal consumer absence
- runtime registration absence
- dynamic/reference absence
- entrypoint/deployment absence
- test/fixture/reference absence
- compatibility requirement absence
- external-consumer risk assessment
- active replacement confirmation
- behavioral equivalence where applicable
- explicit authorization

--------------------------------------------------
NEXT-ACTION PRIORITY
--------------------------------------------------

Priority 1:
    Continue read-only audit of unresolved ai/, controllers/, views/
    and runtime/plugin surfaces.

Priority 2:
    Verify production/runtime wiring where static evidence is insufficient.

Priority 3:
    Resolve external-consumer uncertainty before any source deletion.

Priority 4:
    If and only if explicit authorization is provided, revisit
    repositories/approval.py as a deletion candidate.

--------------------------------------------------
HANDOFF STATUS
--------------------------------------------------

PROVEN:
    - two legacy persistence duplications
    - active replacement layers
    - major capability/execution layering
    - Copilot layering
    - rule-engine compatibility facade
    - no additional safe consolidation

PARTIALLY_EVIDENCED:
    - production runtime topology
    - complete user flow
    - commercial readiness
    - risk-policy semantic convergence

UNKNOWN:
    - external consumers
    - unresolved ai/controllers/views runtime usage
    - complete plugin runtime behavior

BLOCKED:
    - source deletion
    - consolidation
    - schema/data changes
    - dependency/config/Docker changes
    - compatibility removal

NEXT PHASE:
    Continue evidence-gated audit; do not perform cleanup by assumption.

==================================================
PHASE
==================================================

PHASE D — ARCHITECTURE CLEANUP AUDIT AND PLAN

OBJECTIVE:
Based on evidence from previous phases, determine which architectural cleanup is justified, which is premature, and what target architecture can be reached incrementally.

Do not redesign the system from scratch.

==================================================
KNOWN ARCHITECTURE
==================================================

Current system appears hybrid:

api
→ application
→ domain
→ repositories / infrastructure

with additional:

services
execution
capabilities
agents
rule_engine
validators
plugins

Known dependency patterns include:

application → services
services → application
application → repositories
services → repositories
repositories → infrastructure
infrastructure → application
application → infrastructure
execution → infrastructure
application → execution
plugins → rule_engine/domain/validators
agents → domain/rule_engine

These are evidence points, not automatically defects.

==================================================
AUDIT
==================================================

Determine:

1. Actual architectural layers
2. Actual dependency directions
3. Intentional exceptions
4. Accidental coupling
5. Transitional architecture
6. Compatibility architecture
7. Domain leakage
8. Infrastructure leakage
9. Service/application overlap
10. Composition-root responsibilities
11. Runtime registration boundaries
12. Plugin boundaries
13. Execution/worker boundaries
14. Persistence boundaries
15. API/application boundaries
16. Tenant/security boundaries

==================================================
OUTPUT
==================================================

1. CURRENT ARCHITECTURE MAP

2. ACTUAL DEPENDENCY GRAPH

3. INTENTIONAL COUPLING

4. SUSPICIOUS COUPLING

5. TRANSITIONAL LAYERS

6. COMPATIBILITY LAYERS

7. ARCHITECTURAL DEBT

8. WHAT MUST NOT BE TOUCHED YET

9. ARCHITECTURE CLEANUP CANDIDATES

10. TARGET ARCHITECTURE

Target architecture must be evidence-driven.
Do not invent a generic clean architecture.

11. MIGRATION ORDER

For each migration:

MIGRATION_ID =
SCOPE =
MODULES =
CURRENT_STATE =
TARGET_STATE =
PREREQUISITE =
DEPENDENCIES =
RISK =
EXPECTED_BEHAVIOR_IMPACT =
TESTS =
ROLLBACK =
STOP_CONDITION =
AUTHORIZATION_REQUIRED =

12. FINDINGS THAT AFFECT PHASE E

==================================================
STATE CONSISTENCY
==================================================

Compare against previous consolidated state and Phase C.

If contradictory:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = D
PHASE_NAME = ARCHITECTURE_CLEANUP
PHASE_STATUS =

ARCHITECTURE_STATUS =
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

DECISIONS =
DO_NOT_TOUCH =

CURRENT_ARCHITECTURE =
TARGET_ARCHITECTURE =
TRANSITIONAL_LAYERS =
COMPATIBILITY_LAYERS =
ARCHITECTURAL_DEBT =
SAFE_MIGRATIONS =
UNSAFE_OR_PREMATURE_MIGRATIONS =

KEY_FINDINGS =
AFFECTED_FILES =
AFFECTED_MODULES =
DEPENDENCIES_DISCOVERED =
RISKS_DISCOVERED =
OPEN_QUESTIONS =

NEW_EVIDENCE_REQUIRED_FOR_NEXT_PHASE =
INPUT_REQUIRED_BY_NEXT_PHASE =
RECOMMENDED_NEXT_ACTION =

STATE_CHANGE =

C. UPDATED CONSOLIDATED PROJECT STATE

Create self-contained state for Phase E.

Preserve all prior valid findings.

Add:

CURRENT_ARCHITECTURE =
TARGET_ARCHITECTURE =
ARCHITECTURAL_DEBT =
TRANSITIONAL_LAYERS =
COMPATIBILITY_LAYERS =
APPROVED_ARCHITECTURAL_DIRECTIONS =
NOT_APPROVED_ARCHITECTURAL_DIRECTIONS =

Also preserve all cleanup, runtime, UI, product, and commercial states.