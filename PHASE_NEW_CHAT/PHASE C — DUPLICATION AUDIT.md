PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Software Architect specializing in responsibility boundaries, duplication analysis, and incremental modernization.

READ-ONLY ONLY.
DO NOT REFACTOR.

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

AUDIT MODE
= READ-ONLY
= NO SOURCE DELETE EXECUTED

ARCHITECTURE_STATUS
= HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CODE_CLEANUP_STATUS
= NO_SOURCE_DELETE_EXECUTED
+ repositories/approval.py SAFE_TO_DELETE_CANDIDATE

FILE_CLEANUP_STATUS
= CACHE_DELETE_SAFE
+ GENERATED_ARTIFACTS_PARTIALLY_REGENERABLE
+ PERSISTENT_DATA_PROTECTED
+ BACKUP_CANDIDATE_UNVERIFIED

UI_STATUS
= PARTIALLY_EVIDENCED

USER_FLOW_STATUS
= NOT_YET_FULLY_AUDITED

CAPABILITY_STATUS
= NOT_YET_FULLY_AUDITED

COMMERCIAL_READINESS
= PARTIALLY_EVIDENCED

PRODUCTION_READINESS
= PARTIAL / NOT_ESTABLISHED

EXTERNAL_CONSUMER_STATUS
= NOT_FOUND_WITHIN_REPOSITORY_OR_PACKAGE_BOUNDARY
+ OUTSIDE_REPOSITORY_UNKNOWN

DELETION_STATUS
= BLOCKED_PENDING_EXPLICIT_AUTHORIZATION


==================================================
CONFIRMED ENTRYPOINTS / ACTIVE RUNTIME SURFACES
==================================================

CURRENT API CANDIDATE
= app.main

BACKWARD_COMPATIBLE API WRAPPER
= main.py

CURRENT STREAMLIT DASHBOARD
= app.dashboard

BACKWARD_COMPATIBLE DASHBOARD WRAPPER
= dashboard.py

CURRENT WORKER
= worker.py

ACTIVE API COMPOSITION ROOT
= services/container.py

API ROUTERS REGISTERED
= 15

CONFIRMED ACTIVE ROUTER REGISTRATION
= api.main -> app.include_router(...)

CONFIRMED ACTIVE WORKER DEPLOYMENT
= worker.py

CONFIRMED ACTIVE DASHBOARD DEPLOYMENT
= dashboard.py

DYNAMIC PLUGIN DISCOVERY
= plugins.registry
+ importlib.import_module(...)
+ pkgutil.walk_packages(...)


==================================================
CRITICAL AUDIT RULES
==================================================

1. DO NOT classify code as DEAD solely because direct/static imports are zero.

2. Before DEAD classification, consider:
   - static imports
   - reverse imports
   - relative/package imports
   - dynamic imports
   - importlib
   - __import__
   - getattr/reflection
   - registries
   - dependency injection
   - FastAPI route registration
   - Streamlit
   - worker runtime
   - config/env
   - Docker/Compose
   - CI/CD
   - filesystem/templates
   - tests
   - docs
   - entrypoints
   - plugins
   - possible external consumers

3. No repository modification unless explicitly authorized.

4. No deletion/move/rename/refactor.

5. No DB/schema/migration/dependency/config/Docker/API/UI changes.

6. Compatibility shims must not be deleted solely from zero direct imports.

7. Persistent data and migrations remain protected.

8. External consumers outside the repository cannot be proven absent by repository-local evidence alone.


==================================================
LEGACY / CANDIDATE CLASSIFICATIONS
==================================================

repositories/approval.py
= SAFE-TO-DELETE CANDIDATE

Reason:
- both symbols independently audited
- active replacements confirmed
- no internal production consumer found
- no deployment consumer found
- no package export found
- no repository-wide import consumer found
- external consumers outside repository remain UNKNOWN


--------------------------------------------------
repositories.approval.ApprovalRepository
--------------------------------------------------

CLASSIFICATION
= DUPLICATED
+ FUNCTIONALLY_SUPERSEDED
+ ACTIVE_REPLACEMENT_CONFIRMED
+ NO_INTERNAL_PRODUCTION_CONSUMER_PROVEN
+ PACKAGE_EXPORT_ABSENT
+ DEPLOYMENT_CONSUMER_ABSENT
+ EXTERNAL_USAGE_UNKNOWN
+ CONFIDENCE VERY HIGH

ACTIVE REPLACEMENT
= infrastructure.persistence.approval_repository.ApprovalRepository

ACTIVE COMPOSITION ROOT
= services/container.py

ACTIVE BINDING
= self.approval_repository = ApprovalRepository(sessions)

ACTIVE ApprovalService BINDING
= ApprovalService receives self.approval_repository

ACTIVE CONTRACT REQUIRES:
- create(request, token_hash=...)
- get(...)
- update_decision(...)
- list_pending(...)
- list_pending_for_organization(...)
- get_by_execution_id(...)
- get_by_execution_id_for_organization(...)

LEGACY METHOD SURFACE:
- create
- update_decision
- get_by_id
- get_by_execution_id

RUNTIME IDENTITY
= ACTIVE ApprovalRepository is NOT the same object as legacy repositories.approval.ApprovalRepository

SAME_OBJECT
= False


--------------------------------------------------
repositories.approval.RiskPolicyRepository
--------------------------------------------------

CLASSIFICATION
= LEGACY_CANDIDATE
+ FUNCTIONALLY_SUPERSEDED
+ ACTIVE_REPLACEMENT_CONFIRMED
+ NO_PRODUCTION_CONSUMER_PROVEN
+ DOCUMENTED_HISTORICAL_REFERENCE
+ PERSISTENT_SCHEMA_STILL_ACTIVE
+ EXTERNAL_USAGE_UNKNOWN
+ CONFIDENCE HIGH

ACTIVE REPLACEMENT
= infrastructure.persistence.risk_repository.RiskRepository

ACTIVE COMPOSITION ROOT
= services/container.py

ACTIVE BINDING
= self.risk_repository = RiskRepository(sessions)

ACTIVE POLICY CONSUMPTION
= RiskService(policy=self.risk_repository.get_policy())

LEGACY METHOD SURFACE:
- get_active_policy
- save_policy

ACTIVE METHOD SURFACE:
- get_policy

IMPORTANT:
= Legacy repository obsolete does NOT mean risk-policy subsystem/schema is obsolete.


==================================================
PERSISTENT SCHEMA STATUS
==================================================

APPROVAL SCHEMA
= CURRENT / PERSISTENT / PROTECTED

Risk policy schema
= CURRENT / PERSISTENT / PROTECTED

CONFIRMED MODELS:
- ApprovalRecord
- RiskPolicyRecord

CONFIRMED TABLES:
- approvals
- risk_policies

CANONICAL MIGRATION:
= database/migrations/versions/20261002_01_canonical_postgresql_baseline.py

DO NOT DELETE:
- database models for these records
- migrations
- approvals table
- risk_policies table
- persistent data

OPEN ARCHITECTURAL ISSUE:
= risk_policies singleton/selection semantics remain partially unresolved

DOCUMENTATION:
= TARGET_SCHEMA_RECONCILIATION.md
= SCHEMA_DECISION_REGISTER.md


==================================================
OTHER AUDITED CANDIDATES
==================================================

api/schemas.py
= COMPATIBILITY
= HIGH CONFIDENCE
= KEEP

Reason:
= backward-compatible re-export of HTTP response contracts

domain/memory.py
= COMPATIBILITY
= HIGH CONFIDENCE
= KEEP

Reason:
= backward-compatible re-export from domain.agent_memory

application/workflows/queue.py
= UNKNOWN
+ ARCHITECTURAL_PORT
+ ISOLATED_PROTOCOL
+ MEDIUM CONFIDENCE
= KEEP

domain/capability_catalog.py
= CURRENT
+ ARCHITECTURAL_TYPE
+ INTERNAL_USAGE
+ MEDIUM CONFIDENCE
= KEEP

validators/cosmetics.py
= LEGACY_ACTIVE
+ FALLBACK
+ DYNAMIC_USAGE
+ RUNTIME_USAGE_LIKELY
+ HIGH CONFIDENCE
= KEEP

EMPTY __init__.py FILES
= PACKAGE_MARKERS / COMPATIBILITY SURFACES
= NOT DEAD
= KEEP

database/migrations/archive/legacy_versions
= HISTORICAL / DB COMPATIBILITY
= NOT DEAD BY IMPORT COUNT
= KEEP


==================================================
INVALIDATED DEAD-CODE EVIDENCE
==================================================

Previous regex / AST zero-inbound scanners produced large zero-inbound sets.

Those results MUST NOT be used as DEAD-code evidence.

Reason:
- package-level imports were not resolved correctly
- composition-root imports were missed
- router registration was missed
- DI was missed
- dynamic plugin discovery was missed
- active modules such as api.main, services.container, plugins.registry,
  rule_engine and agents incorrectly appeared as zero-inbound

Therefore:

ZERO STATIC INBOUND
!=
DEAD


==================================================
GIT / PACKAGE / DEPLOYMENT EVIDENCE
==================================================

Root project packaging metadata:
= requirements.txt only

No project-level:
- pyproject.toml
- setup.py
- setup.cfg

Current environment distribution metadata:
= project distribution not installed/found

repositories/__init__.py
= does NOT export ApprovalRepository
= does NOT export RiskPolicyRepository

Exports currently include:
- ExecutionRepository
- RuleRepository
- UserRepository

Deployment surfaces:
- Dockerfile -> api.main
- docker-compose.yml -> dashboard.py
- docker-compose.prod.yml -> dashboard.py + worker.py
- CI -> worker.py + tests

No production/deployment import found for:
= repositories.approval


==================================================
GIT HISTORY LIMITATION
==================================================

repositories/approval.py
= tracked
= introduced in f2f5ec2
= feat: Implement risk assessment and approval workflow

infrastructure/persistence/approval_repository.py
= same feature lineage
= later modified by additional commits

IMPORTANT:
= broken refs exist under refs/codex/turn-diffs/checkpoints/...

git log --all was partially blocked by:
= fatal: bad object refs/codex/turn-diffs/checkpoints/...

DO NOT repair/delete/modify broken refs during this audit.

Git history therefore remains:
= PARTIALLY_EVIDENCED


==================================================
TEST BASELINE
==================================================

994 passed
0 failed
0 errors
0 skipped
0 warnings

Interpretation:
= regression baseline is clean

BUT:
= does NOT prove production readiness
= does NOT prove absence of dead code
= does NOT prove absence of external consumers


==================================================
FINAL STATUS
==================================================

PROVEN
= repositories/approval.py is a SAFE-TO-DELETE CANDIDATE
  within the repository/deployment/package boundary

PROVEN
= active ApprovalRepository replacement is infrastructure.persistence.approval_repository.ApprovalRepository

PROVEN
= active RiskRepository replacement is infrastructure.persistence.risk_repository.RiskRepository

PROVEN
= legacy repository classes are not exported by repositories/__init__.py

PROVEN
= persistent approval/risk-policy schemas remain current/protected

PARTIALLY_EVIDENCED
= global absence of external consumers

UNKNOWN
= consumers outside repository/workspace

BLOCKED
= actual source deletion

NEXT ACTION
= explicit authorization gate before deleting repositories/approval.py


==================================================
PHASE B HANDOFF
==================================================

PHASE
= B — CONFIRMED DEAD CODE / LEGACY AUDIT

MODE
= READ-ONLY

SOURCE DELETE
= NOT EXECUTED

PRIMARY RESULT
= repositories/approval.py SAFE-TO-DELETE CANDIDATE

CRITICAL FINDING
= repositories/approval.py contains two legacy repository implementations:
  1. ApprovalRepository
  2. RiskPolicyRepository

Both have confirmed active replacements under infrastructure/persistence.

ApprovalRepository:
= FUNCTIONALLY_SUPERSEDED BY infrastructure.persistence.approval_repository.ApprovalRepository

RiskPolicyRepository:
= FUNCTIONALLY_SUPERSEDED BY infrastructure.persistence.risk_repository.RiskRepository

No internal production consumer was found for either legacy implementation.

No package export was found.

No Docker/Compose/CI/CD consumer was found.

Runtime composition root confirms the infrastructure implementations are the active bindings.

Persistent DB/schema surfaces remain active and protected.

DO NOT infer that deleting the legacy repository means deleting:
- ApprovalRecord
- RiskPolicyRecord
- approvals
- risk_policies
- migrations
- persistent data
- RiskRepository
- ApprovalService


==================================================
AUTHORIZATION BOUNDARY
==================================================

ACTUAL DELETION IS NOT AUTHORIZED YET.

Required explicit authorization:

"Ủy quyền xóa repositories/approval.py."

Until that exact intent is established:

= DO NOT DELETE
= DO NOT MOVE
= DO NOT RENAME
= DO NOT REFACTOR
= DO NOT MODIFY SOURCE

If deletion is later explicitly authorized, perform a final safety gate first:
1. verify target/hash
2. verify final references
3. verify active replacement bindings
4. verify package exports
5. delete ONLY repositories/approval.py
6. run targeted approval/risk tests
7. run full regression
8. inspect git diff/status
9. report exact changes
10. do not alter DB/schema/migrations/config/dependencies


==================================================
STATE CLASSIFICATION
==================================================

PROVEN
= internal functional supersession of repositories/approval.py

PARTIALLY_EVIDENCED
= external-consumer absence
= complete risk-policy semantic convergence

UNKNOWN
= consumers outside repository/workspace

BLOCKED
= actual deletion pending explicit authorization

NEXT ACTION
= authorization gate OR continue READ-ONLY audit of remaining legacy/compatibility surfaces

==================================================
PHASE
==================================================

PHASE C — DUPLICATION AND RESPONSIBILITY OVERLAP AUDIT

OBJECTIVE:
Identify duplicated business logic, overlapping responsibilities, parallel implementations, transitional layers, compatibility layers, and competing abstractions.

Do not modify anything.

==================================================
FOCUS
==================================================

Inspect:

- application/
- services/
- domain/
- repositories/
- infrastructure/
- execution/
- capabilities/
- agents/
- rule_engine/
- validators/
- plugins/
- models/
- schemas/
- API routes
- compatibility wrappers

KNOWN CONCERN:

application <-> services has bidirectional dependencies.

Do not automatically label this as incorrect.

Determine actual responsibility and runtime usage first.

==================================================
LOOK FOR
==================================================

- duplicate CRUD/business logic
- duplicate validation
- duplicate mapping/normalization
- duplicate workflow execution
- duplicate authorization
- duplicate persistence access
- duplicate rule evaluation
- duplicate reporting
- duplicate AI orchestration
- duplicate repository patterns
- old/new implementations
- compatibility wrappers
- parallel service implementations
- duplicated schemas/models
- duplicated API behavior
- responsibility leakage

==================================================
FOR EACH OVERLAP
==================================================

Provide:

IMPLEMENTATION_A =
IMPLEMENTATION_B =
RESPONSIBILITY =
CALLERS =
RUNTIME_USAGE =
TESTS =
DIFFERENCES =
COMPATIBILITY_REASON =
CAN_REPLACE =
EVIDENCE_LEVEL =

==================================================
CLASSIFICATION
==================================================

CURRENT_UNIQUE
CURRENT_DUPLICATED
LEGACY_ACTIVE
COMPATIBILITY
HISTORICAL
UNKNOWN

Do not recommend consolidation merely because two implementations look similar.

==================================================
OUTPUT
==================================================

1. EXECUTIVE SUMMARY

2. DUPLICATION MATRIX

3. RESPONSIBILITY MAP

4. APPLICATION VS SERVICES

5. DOMAIN VS SERVICE LOGIC

6. RULE_ENGINE VS VALIDATORS

7. AGENTS VS AI/COPILOT

8. REPOSITORY/PERSISTENCE OVERLAPS

9. API/SERVICE OVERLAPS

10. SAFE CONSOLIDATION CANDIDATES

11. NOT_SAFE_TO_CONSOLIDATE

12. REQUIRES_RUNTIME_VERIFICATION

13. FINDINGS THAT AFFECT PHASE D

==================================================
STATE CONSISTENCY
==================================================

Compare with previous consolidated state and Phase B handoff.

If contradiction:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Never silently overwrite prior evidence.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = C
PHASE_NAME = DUPLICATION_AND_RESPONSIBILITY
PHASE_STATUS =

CODE_CLEANUP_STATUS =
ARCHITECTURE_STATUS =

SAFE_TO_DELETE_NOW =
SAFE_TO_CONSOLIDATE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

PROVEN =
PARTIALLY_EVIDENCED =
UNKNOWN =
BLOCKED =

B. PHASE HANDOFF

PHASE_ID =
PHASE_NAME =
PHASE_STATUS =

OBJECTIVE =
SCOPE_AUDITED =

PROVEN =
PARTIALLY_EVIDENCED =
UNKNOWN =
BLOCKED =

CONFIRMED_DUPLICATED =
CURRENT_UNIQUE =
LEGACY_ACTIVE =
COMPATIBILITY =
HISTORICAL =
UNKNOWN_OVERLAPS =

DO_NOT_TOUCH =
SAFE_TO_CONSOLIDATE_NOW =

REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

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

Create self-contained state for Phase D.

Preserve all previous valid findings.

Add:

KNOWN_DUPLICATION =
KNOWN_RESPONSIBILITY_OVERLAP =
KNOWN_TRANSITIONAL_LAYERS =
KNOWN_COMPATIBILITY_LAYERS =
KNOWN_ARCHITECTURAL_DEBT =

Also preserve:

CURRENT =
LEGACY_OR_INVESTIGATION =
HISTORICAL =
DEAD_CONFIRMED =
PROTECTED_DATA =
UNKNOWN =
BLOCKED =

SAFE_TO_DELETE_NOW =
SAFE_TO_CONSOLIDATE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =