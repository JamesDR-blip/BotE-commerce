PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Bạn là Senior Software Architect + Repository Auditor.
Đây là READ-ONLY AUDIT.
Không được sửa repository.

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
PREVIOUS CONSOLIDATED STATE
==================================================

Nếu đây là Phase A đầu tiên:
PREVIOUS CONSOLIDATED STATE = NONE

==================================================
PHASE
==================================================

PHASE A — SAFE FILE CLEANUP AUDIT

OBJECTIVE:
Xác định các file/directory/generated artifacts có thể cleanup an toàn mà không ảnh hưởng runtime, persistence, tests, deployment, documentation hoặc external workflows.

DO NOT MODIFY ANYTHING.

==================================================
SCOPE
==================================================

Audit:

- .hypothesis/
- .pytest_cache/
- .ruff_cache/
- .mypy_cache/
- __pycache__/
- pytest temporary directories
- artifacts/
- reports/
- generated reports
- logs
- local databases
- Chroma state
- build/cache outputs
- temporary files
- suspicious root-level artifacts
- other generated/local files discovered during audit

Do not assume a file is disposable because:
- it looks generated
- it is old
- it is not imported
- it is not source code
- it is large
- it is ignored by Git

==================================================
CHECK
==================================================

For each candidate inspect where possible:

1. Git tracked/untracked/ignored status
2. Source references
3. Test references
4. Docker/Compose references
5. CI/CD references
6. Script references
7. Configuration references
8. Runtime persistence role
9. Whether it is reproducible
10. Whether deletion changes behavior
11. Whether it contains user/business data
12. Whether it is required for local development
13. Whether it is required for deployment
14. Whether it is audit/evidence output
15. Whether external consumers are possible
16. Whether deletion requires explicit authorization

Never send or request .env secrets.

==================================================
CLASSIFICATION
==================================================

Each candidate must be classified as exactly one:

SAFE_TO_DELETE
SAFE_TO_REGENERATE
PROTECTED
REQUIRES_MORE_EVIDENCE
UNKNOWN

For every classification provide evidence.

==================================================
OUTPUT
==================================================

1. EXECUTIVE SUMMARY

2. FILE CLEANUP MATRIX

Columns:

PATH
TYPE
GIT_STATUS
SOURCE_REFERENCE
TEST_REFERENCE
RUNTIME_REFERENCE
PERSISTENCE_ROLE
REGENERABLE
EXTERNAL_CONSUMER_RISK
RISK
CLASSIFICATION
EVIDENCE

3. SAFE_TO_DELETE_NOW

4. SAFE_TO_REGENERATE

5. PROTECTED_FILES

6. REQUIRES_MORE_EVIDENCE

7. REQUIRES_RUNTIME_VERIFICATION

8. REQUIRES_EXPLICIT_AUTHORIZATION

9. FILES/MODULES THAT MUST NOT BE TREATED AS DEAD CODE

10. FINDINGS THAT MAY AFFECT PHASE B

==================================================
STATE CONSISTENCY RULE
==================================================

Compare findings against PREVIOUS CONSOLIDATED STATE.

If there is no contradiction:
STATE_CHANGE = NONE

If new evidence contradicts an existing state:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Do not silently overwrite previous findings.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = A
PHASE_NAME = SAFE_FILE_CLEANUP
PHASE_STATUS =
FILE_CLEANUP_STATUS =

SAFE_TO_DELETE_NOW =
SAFE_TO_REGENERATE =
PROTECTED =
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

DECISIONS =
DO_NOT_TOUCH =

SAFE_TO_DELETE_NOW =
SAFE_TO_MODIFY_NOW =

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

BASELINE_IMPACT =

STATE_CHANGE =

C. UPDATED CONSOLIDATED PROJECT STATE

Produce a compact but complete current state that Phase B can use without access to this chat.

Must preserve all still-valid previous findings.

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

SAFE_TO_DELETE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

CURRENT =
COMPATIBILITY =
LEGACY_OR_INVESTIGATION =
PROTECTED_DATA =
KNOWN_ARCHITECTURAL_DEBT =
KNOWN_RUNTIME_RISKS =
KNOWN_PRODUCT_GAPS =
UNKNOWN =
BLOCKED =

Do not remove unresolved items merely because they were not relevant to Phase A.