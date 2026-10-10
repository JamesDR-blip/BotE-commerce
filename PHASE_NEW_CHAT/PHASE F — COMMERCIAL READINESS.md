PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Product Architect + Production Readiness Auditor + Technical Due-Diligence Auditor.

READ-ONLY ONLY.
DO NOT MODIFY PROJECT.

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

PROJECT:
Autonomous E-commerce Data Operations Platform

AUDIT MODE:
READ-ONLY / EVIDENCE-FIRST

NO SOURCE / CONFIG / SCHEMA / DEPENDENCY / DOCKER / API / UI
MODIFICATIONS AUTHORIZED.

==================================================
1. GLOBAL ARCHITECTURE STATE
==================================================

ARCHITECTURE:
HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CURRENT ARCHITECTURAL MODEL:

API / UI
   ↓
Application / Use-case orchestration
   ↓
Domain

Cross-cutting:
- authorization
- policy
- risk
- ports

Execution:
Application
   ↓
Agents
   ↓
Execution
   ↓
Capability registry
   ↓
Domain capabilities

Infrastructure:
- persistence / repositories
- queue / Redis
- storage
- external adapters

Composition root:
services.container

IMPORTANT:
services.container is an ACTIVE composition root and must be preserved.

==================================================
2. CLEANUP DECISION
==================================================

GLOBAL CLEANUP STATUS:

NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

No source file/package has reached:

DEAD_CONFIRMED
+
NO_INTERNAL_CONSUMER
+
NO_DYNAMIC/RUNTIME_ROLE
+
NO_COMPATIBILITY_ROLE
+
NO_EXTERNAL_CONSUMER EVIDENCE
+
NO_PERSISTENCE/OPERATIONAL ROLE

Therefore:

NO DELETE
NO MOVE
NO RENAME
NO COMPATIBILITY REMOVAL
NO PACKAGE CONSOLIDATION

without additional evidence and explicit authorization.

==================================================
3. PROVEN CURRENT / CRITICAL SURFACES
==================================================

PROVEN CURRENT:

- app.main
- app.dashboard
- app.api_client
- dashboard.py compatibility entrypoint
- worker.py
- services.container
- plugins.registry
- FastAPI application
- 15 API router areas
- workflow execution infrastructure
- application/domain/execution layers
- active infrastructure/persistence paths
- approval services
- ChangeSet services
- rollback services
- channel/sync services
- marketplace services
- lineage services
- audit services

CRITICAL RUNTIME SURFACES:

- worker.py
- services.container
- plugins.registry
- workflow execution / Redis consumer topology

KEEP.

==================================================
4. PROVEN API CAPABILITIES
==================================================

PROVEN:

Authentication/authorization infrastructure:
- backend authorization mechanisms exist
- API client supports Authorization header
- workflow services perform authorization

Organizations / workspace / project:
- backend evidence exists
- workspace/project discovery is partially exposed in UI

Datasets:
- create
- ingest/upload
- get
- list

Data operations:
- upload
- clean
- extract
- mapping
- validate
- validations

Validation:
- API
- Streamlit UI
- report retrieval

Workflow:
- author
- save
- version
- list versions
- activate
- simulate
- execute sync
- execute async
- execution status
- execution detail

Queued execution:
- Redis workflow execution queue
- Redis consumer
- worker
- recovery worker

Governance:
- risk assessment
- approval request
- pending approval
- approve
- reject
- decision
- ChangeSet
- rollback

Channels:
- list channels
- start sync
- sync job status

Marketplace:
- list packages
- install package

Observability:
- dataset lineage
- audit logs

Rules / risk / monitoring:
- backend/API evidence exists

Copilot:
- session
- chat
- SSE streaming
- governed action context exists

==================================================
5. PROVEN UI SURFACE
==================================================

CURRENT UI:
app.dashboard

UI CHARACTERIZATION:

QUALITY-CENTRIC OPERATIONAL DASHBOARD WITH COPILOT

PROVEN USER JOURNEYS:

1. Validation
   Upload CSV/XLS/XLSX
   ↓
   Category selection
   ↓
   Validate
   ↓
   Result / health score
   ↓
   Execution ID
   ↓
   Report download

2. Data Health
   Workspace
   ↓
   Project
   ↓
   Dataset
   ↓
   Health metrics
   ↓
   Diagnostics
   ↓
   Remediation preview

3. AI Copilot
   Session
   ↓
   Chat
   ↓
   Streaming response
   ↓
   governed action/status context

4. Execution History
   History retrieval
   ↓
   execution visibility

PROVEN UI CONTROLS:

- file uploader
- selectbox
- text input
- validation button
- report download
- dataset/project selection
- chat input
- AI Copilot expander
- health/diagnostics rendering
- execution history

==================================================
6. UI COVERAGE GAP
==================================================

Backend capability is materially broader than currently proven UI capability.

NOT PROVEN AS COMPLETE USER-FACING JOURNEYS:

- workflow authoring UI
- workflow versioning UI
- workflow activation UI
- workflow simulation UI
- workflow execution UI
- approval decision UI
- ChangeSet management UI
- rollback UI
- channel management UI
- sync management UI
- marketplace UI
- lineage UI
- audit-log UI
- cleaning UI
- extraction UI
- mapping UI
- complete dataset lifecycle UI
- complete risk-management UI

IMPORTANT:

Absence from Streamlit dashboard DOES NOT imply dead backend code.

These are currently PRODUCT/UI COVERAGE GAPS unless additional evidence proves otherwise.

==================================================
7. DASHBOARD ERROR / STATE COVERAGE
==================================================

PROVEN:

- loading states
- error states
- empty states
- unavailable backend states
- report unavailable state
- project loading errors
- health metric errors
- diagnostic errors
- Copilot session errors
- Copilot streaming errors
- history errors
- validation errors

PARTIALLY_EVIDENCED:

- explicit recovery/retry behavior
- reload/refresh mechanisms
- complete recovery journey

==================================================
8. AUTH / TENANT / PERMISSION STATE
==================================================

PROVEN:

- backend authorization mechanisms
- API client Authorization header support
- workflow/application authorization logic

PARTIALLY_EVIDENCED:

- workspace-aware UI
- workspace/project context

UNKNOWN:

- login UX
- token acquisition UX
- token/session lifecycle
- organization UI
- tenant UI
- permission UI
- permission-denied UX
- tenant isolation in actual runtime
- user-visible authorization state

IMPORTANT:

workspace_id input is NOT proof of tenant isolation.

No security defect is asserted from the static evidence.

==================================================
9. WORKFLOW / RUNTIME TOPOLOGY
==================================================

PROVEN STATIC TOPOLOGY:

API
 ↓
WorkflowRuntimeService
 ↓
workflow execution / queue
 ↓
RedisWorkflowExecutionConsumer
 ↓
worker.py
 ↓
build_container()
 ↓
WorkflowExecutionWorker.run/recover
 ↓
execution/workflow/engine.py

Also proven:

services.container wires:
- WorkflowEngine
- WorkflowExecutionWorker
- Redis-backed workflow consumer dependencies

UNKNOWN:

- actual production deployment
- Redis reachability
- real production job consumption
- worker recovery under deployment conditions

==================================================
10. DYNAMIC IMPORT AUDIT
==================================================

PRODUCTION DYNAMIC IMPORTS IDENTIFIED:

1. application/copilot/service.py
   - __import__("datetime")
   - CURRENT
   - PROVEN
   - no legacy risk identified

2. plugins/registry.py
   - importlib.import_module
   - pkgutil.walk_packages
   - active plugin/validator discovery
   - CURRENT
   - PROVEN
   - CRITICAL

No other production dynamic-import surface was identified by the completed audit.

KEEP plugins.registry.

==================================================
11. COMPATIBILITY / LEGACY REGISTER
==================================================

dashboard.py
Classification:
COMPATIBILITY
Evidence:
PROVEN
Decision:
KEEP

/history
Classification:
CURRENT + COMPATIBILITY
Evidence:
PROVEN
Decision:
KEEP

/report/{id}/{format}
Classification:
CURRENT + COMPATIBILITY
Evidence:
PROVEN
Decision:
KEEP

validate_alias
Classification:
COMPATIBILITY
Evidence:
PROVEN
Decision:
KEEP pending consumer evidence

repositories/approval.py
Classification:
LEGACY / COMPATIBILITY CANDIDATE
Evidence:
PARTIALLY_EVIDENCED
Decision:
KEEP TEMPORARILY
Next:
TRACE CONSUMERS → DEPRECATE → REMOVE ONLY WITH AUTHORIZATION

RiskPolicyRepository
Classification:
UNKNOWN / LEGACY CANDIDATE
Evidence:
PARTIALLY_EVIDENCED
Decision:
TRACE SEPARATELY

ai/
Classification:
UNKNOWN / LEGACY CANDIDATE
Evidence:
PARTIALLY_EVIDENCED
Decision:
KEEP / TRACE

controllers/
Classification:
UNKNOWN / LEGACY CANDIDATE
Evidence:
PARTIALLY_EVIDENCED
Decision:
KEEP / TRACE

views/
Classification:
UNKNOWN / LEGACY CANDIDATE
Evidence:
PARTIALLY_EVIDENCED
Decision:
KEEP / TRACE

==================================================
12. APPROVAL REPOSITORY CONCLUSION
==================================================

CURRENT:

infrastructure/persistence/approval_repository.py

PROVEN capabilities:
- session factory
- create
- decision update
- expiration enforcement
- decision validation
- organization-scoped queries
- execution/workflow/project/workspace/organization lookup chain
- pending approvals

LEGACY CANDIDATE:

repositories/approval.py

Differences include:
- older direct Session pattern
- incomplete decision update semantics
- older repository surface
- current infrastructure implementation provides materially stronger governance behavior

IMPORTANT:

No direct internal import of repositories.approval was found.

However:

NO DIRECT IMPORT ≠ PROOF OF DEAD CODE

External compatibility consumers remain UNKNOWN.

==================================================
13. PERSISTENT / INFRASTRUCTURE DATA
==================================================

data_quality.db:
Classification:
PERSISTENT DATA / OPERATIONAL UNKNOWN

Decision:
DO NOT DELETE.

chroma/:
Classification:
PERSISTENT / INFRASTRUCTURE UNKNOWN

Decision:
DO NOT DELETE.

Required evidence:
- runtime configuration
- production exposure
- persistence ownership
- migration/lifecycle behavior

==================================================
14. TEST BASELINE
==================================================

Current known test result:

994 passed
0 failed
0 errors
0 skipped
0 warnings

Interpretation:

PROVES:
- tested regression suite is green

DOES NOT PROVE:
- production readiness
- deployment correctness
- complete UI journey
- tenant isolation
- security isolation
- production worker E2E
- commercial readiness
- unused legacy code absence

==================================================
15. PRODUCT / UX CONCLUSION
==================================================

The platform currently demonstrates:

STRONGER BACKEND / API CAPABILITY
than
PROVEN USER-FACING PRODUCT COVERAGE.

Current Streamlit UI is best characterized as:

QUALITY-CENTRIC OPERATIONAL DASHBOARD WITH COPILOT

It is NOT yet proven to be a complete:
- Data Operations console
- Workflow authoring console
- Governance console
- Integration console
- Marketplace console
- Lineage/audit console

This is a product coverage finding,
not a dead-code finding.

==================================================
16. PROVEN / PARTIALLY_EVIDENCED / UNKNOWN / BLOCKED
==================================================

PROVEN:

- active FastAPI backend
- 15 API router areas
- Streamlit dashboard
- validation journey
- report journey
- Data Health
- diagnostics
- Copilot conversation
- execution history
- data operations APIs
- dataset lifecycle APIs
- workflow backend
- queued execution topology
- worker entrypoint
- approval/governance backend
- ChangeSet/rollback
- channels/sync
- marketplace
- lineage
- audit
- plugin discovery
- composition root
- compatibility surfaces
- significant UI state handling
- no DEAD_CONFIRMED source file

PARTIALLY_EVIDENCED:

- complete user journey
- workflow UI
- governance UI
- dataset/Data Operations UI
- Copilot governed action completion
- production runtime topology
- recovery UX
- legacy repository migration
- compatibility retirement
- workspace-aware UX
- approval ↔ ChangeSet complete E2E

UNKNOWN:

- external compatibility consumers
- production Redis E2E
- effective production DATABASE_URL
- production migration behavior
- Chroma production role/configuration
- login/token UX
- tenant/org UX
- permission-denied UX
- actual browser runtime
- complete workflow UI
- complete approval UI
- complete integration/marketplace UI
- whether API-only capabilities are intentionally admin/integration/automation surfaces

BLOCKED:

Any destructive cleanup requiring:
- explicit authorization
- missing consumer evidence
- missing runtime evidence
- schema/data migration decision
- compatibility retirement approval

==================================================
17. FINAL CLEANUP DECISION
==================================================

NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

NO PACKAGE SAFE TO DELETE

NO COMPATIBILITY SURFACE SAFE TO REMOVE

NO BROAD REWRITE JUSTIFIED

RECOMMENDED STRATEGY:

PRESERVE
 ↓
TRACE CONSUMERS
 ↓
ESTABLISH RUNTIME / PRODUCTION EVIDENCE
 ↓
CONVERGE TRANSITIONAL LAYERS
 ↓
DEPRECATE COMPATIBILITY SURFACES
 ↓
REMOVE ONLY AFTER EXPLICIT AUTHORIZATION

==================================================
PHASE E HANDOFF
==================================================

OBJECTIVE:
Audit actual UI/user journey/capability coverage against the
broader backend/API platform surface.

STATUS:
COMPLETE

AUDIT MODE:
READ-ONLY

==================================================
PHASE E CONCLUSION
==================================================

PRIMARY FINDING:

Backend/platform capability maturity is materially greater than
currently proven user-facing UI coverage.

The Streamlit dashboard is a narrow, quality-centric operational
surface with Copilot.

Backend APIs/application services provide substantially broader
Data Operations, Workflow, Governance, Integration, Marketplace,
Lineage and Audit capabilities.

==================================================
E6-A — WORKFLOW
==================================================

PROVEN:

- workflow creation
- workflow retrieval/listing
- workflow versions
- version activation
- simulation
- synchronous execution
- asynchronous execution
- execution status
- execution detail
- authorization
- organization resolution
- risk/governance integration
- execution constraints/quota
- approval integration

PARTIALLY_EVIDENCED:

Complete user-facing workflow journey.

UNKNOWN:

Whether workflow capabilities are intentionally API/admin/
integration surfaces rather than Streamlit user journeys.

DECISION:

DO NOT CLEAN UP workflow backend because UI controls are absent.

==================================================
E6-B — GOVERNANCE
==================================================

PROVEN:

Approval:
- request
- pending
- decision
- approve
- reject

Governance:
- authorization
- approver role
- token validation
- expiration
- organization scope

ChangeSet:
- preparation
- immutable ChangeSet semantics
- approval integration

Rollback:
- rollback
- ownership/authorization checks

PARTIALLY_EVIDENCED:

Full approval → ChangeSet → execution → audit E2E.

UI currently exposes approval/risk/ChangeSet status context.

UNKNOWN:

Approver's complete UI journey.

DECISION:

Keep governance backend/services.
Do not infer dead code from missing dashboard controls.

==================================================
E6-C — DATA / DATASET
==================================================

PROVEN API:

Data operations:
- upload
- clean
- extract
- mapping
- validate
- validations

Dataset lifecycle:
- create
- upload/ingest
- get
- list by project

PROVEN UI:

- upload
- category selection
- validation
- report/result
- Data Health
- diagnostics

PARTIALLY_EVIDENCED:

Single complete user journey connecting dataset ingestion,
cleaning/extraction/mapping/validation/health.

DECISION:

Do not delete data operation or dataset services/APIs.

==================================================
E6-D — INTEGRATION / OBSERVABILITY
==================================================

PROVEN:

Channels:
- list channels
- start sync
- retrieve sync job

Marketplace:
- list marketplace packages
- install marketplace package

Lineage:
- dataset lineage endpoint

Audit:
- audit log endpoint

Application services are directly wired from routes.

PARTIALLY_EVIDENCED:

Complete user-facing integration/observability journeys.

UNKNOWN:

Whether these are intentionally API-only/admin/integration surfaces.

DECISION:

Do not classify these backend capabilities as dead due to absent UI.

==================================================
E6-E — UI DISCOVERABILITY
==================================================

PROVEN UI controls:

- file uploader
- category selectbox
- validation button
- report download
- workspace input
- project selection
- dataset selection
- chat input
- AI Copilot
- health/diagnostic displays
- execution history

NO CURRENT DASHBOARD CONTROL PROVEN FOR:

- workflow authoring
- workflow simulation
- workflow execution
- approval decision
- ChangeSet management
- rollback
- channels
- sync
- risk management
- lineage
- audit
- marketplace

IMPORTANT:

"Not found in app/dashboard.py"
means:

UI NOT PROVEN

It does NOT mean:

BACKEND DEAD

==================================================
CAPABILITY MATRIX
==================================================

Authentication:
Backend PROVEN
UI UNKNOWN

Authorization:
Backend PROVEN
UI UNKNOWN

Organizations:
Backend PROVEN
UI UNKNOWN

Workspaces:
Backend PROVEN
UI PARTIAL

Projects:
Backend PROVEN
UI PROVEN
Full journey PARTIAL

Datasets:
Backend PROVEN
UI PARTIAL
Full journey PARTIAL

Channels:
Backend PROVEN
UI UNKNOWN

Mappings:
Backend PROVEN
UI UNKNOWN

Sync:
Backend PROVEN
UI UNKNOWN

Workflow:
Backend PROVEN
UI UNKNOWN

Queued execution:
Backend PROVEN
UI PARTIAL

Validation:
Backend PROVEN
UI PROVEN
User journey PROVEN

Rules:
Backend PROVEN
UI UNKNOWN

Semantic search:
Backend evidence exists
UI UNKNOWN

AI/Copilot:
Backend PROVEN
UI PROVEN
Complete governed action journey PARTIAL

ChangeSets:
Backend PROVEN
UI PARTIAL

Approvals:
Backend PROVEN
UI PARTIAL

Risk:
Backend PROVEN
UI PARTIAL

Audit:
Backend PROVEN
UI UNKNOWN

Lineage:
Backend PROVEN
UI UNKNOWN

Reports:
Backend PROVEN
UI PROVEN

Exports:
PARTIAL

Monitoring:
Backend/API PROVEN
UI PARTIAL

Configuration:
Backend PROVEN
UI PARTIAL

Integrations/Marketplace:
Backend PROVEN
UI UNKNOWN

==================================================
UX STATE AUDIT
==================================================

PROVEN:

Loading:
- validation
- Copilot
- health/data loading paths

Error:
- backend unavailable
- project load
- health metrics
- diagnostics
- Copilot session
- Copilot stream
- history
- validation

Empty:
- no workspace/project information
- no projects
- no datasets
- no diagnostics
- no remediation
- no executions

PARTIALLY_EVIDENCED:

Recovery:
- explicit retry
- refresh
- reload
- recovery action

==================================================
PHASE E RISK ASSESSMENT
==================================================

HIGH RISK MISINTERPRETATION TO AVOID:

"Backend capability has no Streamlit UI"
≠
"Backend capability is dead."

Correct interpretation:

"Backend capability is proven, but complete user-facing reachability
is not proven."

==================================================
PHASE E OUTPUT FOR CLEANUP
==================================================

DO NOT DELETE:

- workflow backend
- governance backend
- data operation services
- dataset services
- channel/sync services
- marketplace services
- lineage/audit services
- worker
- composition root
- plugin registry
- current dashboard
- compatibility entrypoints
- persistent stores

TRACE BEFORE ANY FUTURE REMOVAL:

- repositories/approval.py
- RiskPolicyRepository
- ai/
- controllers/
- views/
- repository compatibility surfaces
- external consumers

==================================================
PHASE E HANDOFF TO NEXT PHASE
==================================================

NEXT OBJECTIVE:

Convert the audit findings into an evidence-backed convergence/
cleanup execution plan without performing any modifications.

FIRST PRIORITY:

1. Consumer tracing for repositories/approval.py.
2. Consumer tracing for RiskPolicyRepository.
3. Consumer tracing for ai/.
4. Consumer tracing for controllers/.
5. Consumer tracing for views/.
6. Identify remaining repository compatibility surfaces.
7. Map each legacy candidate to its current replacement.
8. Establish deprecation criteria.
9. Only after evidence is sufficient, prepare removal candidates.

SECOND PRIORITY:

Establish runtime evidence for:

- production Compose topology
- DATABASE_URL
- migration strategy
- Redis worker E2E
- Chroma configuration
- actual dashboard runtime
- authentication/session behavior
- tenant/organization isolation

THIRD PRIORITY:

Convergence planning:

- DataOperationsService boundary
- application/service coupling
- repository normalization
- governance/risk DI
- compatibility retirement

==================================================
NEXT-PHASE GUARDRAILS
==================================================

READ-ONLY.

NO:
- delete
- move
- rename
- refactor
- dependency changes
- config changes
- Docker changes
- API behavior changes
- schema changes
- migration changes
- UI changes

External consumer absence must be evidenced before compatibility removal.

No direct import must never be treated as proof of dead code.

Persistent data must be protected until runtime ownership is proven.

==================================================
FINAL PHASE E HANDOFF STATUS
==================================================

PHASE E:
COMPLETE

ARCHITECTURE:
HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CLEANUP:
NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

PRODUCT:
BACKEND CAPABILITY > PROVEN UI COVERAGE

PRIMARY NEXT ACTION:
CONSUMER TRACE → REPLACEMENT MAPPING → DEPRECATION EVIDENCE
→ RUNTIME VERIFICATION → AUTHORIZED REMOVAL CANDIDATES

==================================================
PHASE
==================================================

PHASE F — COMMERCIAL READINESS AUDIT

OBJECTIVE:
Determine the evidence level for real customer usage, operational readiness, and commercialization.

Do not provide scores, rankings, or overall subjective verdicts.

Allowed statuses only:

PROVEN
PARTIALLY_EVIDENCED
UNKNOWN
BLOCKED
NOT_APPLICABLE

==================================================
COMMERCIAL CATEGORIES
==================================================

A PRODUCT COMPLETENESS
B UX
C SECURITY
D MULTI-TENANCY
E DATA ISOLATION
F RELIABILITY
G BACKUP/RESTORE
H DEPLOYMENT
I MONITORING
J LOGGING
K ERROR HANDLING
L DOCUMENTATION
M CUSTOMER ONBOARDING
N SUPPORTABILITY
O AI/LLM OPERATIONS
P PERFORMANCE
Q INTEGRATIONS
R COMMERCIALIZATION

==================================================
FOR EACH CATEGORY
==================================================

Determine:

STATUS =
EVIDENCE =
IMPLEMENTATION =
TESTS =
OPERATIONAL_EVIDENCE =
MISSING_EVIDENCE =
RISK =
REQUIRED_VERIFICATION =
CUSTOMER_IMPACT =

Do not infer production readiness from test results alone.

==================================================
SECURITY
==================================================

Inspect evidence for:

- authentication
- authorization
- RBAC
- tenant isolation
- workspace isolation
- dataset isolation
- secret handling
- API security
- persistence isolation
- Chroma/vector-store isolation
- dependency vulnerabilities
- audit logging
- data access boundaries

==================================================
DEPLOYMENT
==================================================

Inspect:

- Dockerfile
- docker-compose
- production compose
- migration process
- startup behavior
- create_all vs Alembic
- worker
- Redis
- PostgreSQL
- health checks
- recovery
- backups
- restore
- observability
- deployment rehearsal

==================================================
PRODUCT PROPOSITION
==================================================

Determine only from evidence:

CURRENT_PRODUCT_PROPOSITION =
CURRENT_TARGET_USER =
CURRENT_CORE_WORKFLOW =
CURRENT_CUSTOMER_VALUE =

If insufficient evidence:
UNKNOWN.

==================================================
OUTPUT
==================================================

1. EXECUTIVE SUMMARY

2. COMMERCIAL READINESS MATRIX

Columns:

CATEGORY
STATUS
EVIDENCE
IMPLEMENTATION
TESTS
OPERATIONAL_EVIDENCE
GAP
RISK
REQUIRED_VERIFICATION

3. CURRENT PRODUCT PROPOSITION

4. CURRENT TARGET USER

5. CURRENT CORE WORKFLOW

6. CURRENT CUSTOMER VALUE

7. MUST_FIX_BEFORE_FIRST_CUSTOMER

8. SHOULD_FIX_BEFORE_PAID_SCALE

9. NICE_TO_HAVE

10. UNKNOWN

11. BLOCKED

12. PRODUCTION READINESS

13. SECURITY READINESS

14. DEPLOYMENT READINESS

15. FINDINGS THAT AFFECT PHASE G

==================================================
STATE CONSISTENCY
==================================================

Compare against:

- Master Context
- Phase E Consolidated State
- Phase E Handoff

If contradiction:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Never silently overwrite prior findings.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = F
PHASE_NAME = COMMERCIAL_READINESS
PHASE_STATUS =

COMMERCIAL_READINESS =
PRODUCTION_READINESS =

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

COMMERCIAL_READINESS_MATRIX =
SECURITY_FINDINGS =
DEPLOYMENT_FINDINGS =
RELIABILITY_FINDINGS =
PRODUCT_FINDINGS =

CURRENT_PRODUCT_PROPOSITION =
CURRENT_TARGET_USER =
CURRENT_CORE_WORKFLOW =
CURRENT_CUSTOMER_VALUE =

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

NEW_EVIDENCE_REQUIRED_FOR_PHASE_G =
INPUT_REQUIRED_BY_PHASE_G =
RECOMMENDED_NEXT_ACTION =

STATE_CHANGE =

C. UPDATED CONSOLIDATED PROJECT STATE

Create the FINAL CONSOLIDATED PROJECT STATE for Phase G.

This must be self-contained.

Preserve all valid findings from A–E.

Include:

PROJECT_AUDIT_STATUS =
ARCHITECTURE_STATUS =
CODE_CLEANUP_STATUS =
FILE_CLEANUP_STATUS =
UI_STATUS =
USER_FLOW_STATUS =
CAPABILITY_STATUS =
COMMERCIAL_READINESS =
PRODUCTION_READINESS =

CURRENT =
COMPATIBILITY =
LEGACY_OR_INVESTIGATION =
HISTORICAL =
DUPLICATED =
DEAD_CONFIRMED =
PROTECTED_DATA =

CURRENT_ARCHITECTURE =
TARGET_ARCHITECTURE =
ARCHITECTURAL_DEBT =
TRANSITIONAL_LAYERS =
COMPATIBILITY_LAYERS =

CURRENT_USER_JOURNEY =
CURRENT_UI_SURFACES =
BACKEND_ONLY_CAPABILITIES =
USER_ACCESSIBLE_CAPABILITIES =
BLOCKED_CAPABILITIES =

CURRENT_PRODUCT_PROPOSITION =
CURRENT_TARGET_USER =
CURRENT_CORE_WORKFLOW =
CURRENT_CUSTOMER_VALUE =

MUST_FIX_BEFORE_FIRST_CUSTOMER =
SHOULD_FIX_BEFORE_PAID_SCALE =
NICE_TO_HAVE =

SAFE_TO_DELETE_NOW =
SAFE_TO_REGENERATE =
SAFE_TO_CONSOLIDATE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

KNOWN_RUNTIME_RISKS =
KNOWN_SECURITY_RISKS =
KNOWN_DEPLOYMENT_RISKS =
KNOWN_PRODUCT_GAPS =
UNKNOWN =
BLOCKED =

IMPLEMENTATION_CANDIDATES =
DO_NOT_IMPLEMENT_YET =

FINAL_RECOMMENDED_NEXT_ACTION =
Proceed to Phase G Master Roadmap and Implementation Planning.