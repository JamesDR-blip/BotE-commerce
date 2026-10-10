PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Software Architect + Dead-Code / Dependency Auditor.

READ-ONLY ONLY.
DO NOT DELETE OR MODIFY CODE.

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

ARCHITECTURE_STATUS
= HYBRID_WITH_ACTIVE_TRANSITIONAL_LAYERS_AND_COMPATIBILITY_SURFACES

CODE_CLEANUP_STATUS
= NO_SOURCE_DELETE_SAFE_TO_APPROVE_YET

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

SAFE_TO_DELETE_NOW
= .hypothesis/
  .pytest_cache/
  .ruff_cache/
  .mypy_cache/
  __pycache__/

SAFE_TO_REGENERATE
= artifacts/  [with caution]

PROTECTED_FILES
= data_quality.db
  chroma/
  database/migrations/archive/legacy_versions/
  reports/
  tracked architectural/migration/audit evidence

REQUIRES_MORE_EVIDENCE
= application/changesets/changeset_service.py.s18-backup
  raw_fashion_data.csv
  test_products.csv
  selected generated audit reports

REQUIRES_RUNTIME_VERIFICATION
= production Compose startup
  worker deployment/recovery
  effective DATABASE_URL
  Alembic vs create_all
  Chroma exposure/config
  actual Streamlit user journey
  plugin runtime loading

REQUIRES_EXPLICIT_AUTHORIZATION
= any deletion/move/rename
  DB/schema/migration/dependency/config/Docker changes
  compatibility-shim removal

==================================================
PHASE A HANDOFF
==================================================

============================================================
PHASE A HANDOFF
SAFE FILE CLEANUP AUDIT
============================================================

PROJECT:
Autonomous E-commerce Data Operations Platform

PHASE:
A — SAFE FILE CLEANUP AUDIT

STATUS:
PHASE_A_COMPLETE_WITH_RESTRICTED_CLEANUP_SCOPE

AUDIT MODE:
READ-ONLY

NO MODIFICATION / DELETION / MOVE / RENAME PERFORMED


============================================================
1. EXECUTIVE DECISION
============================================================

Phase A đã hoàn tất ở mức evidence hiện có.

Kết luận chính:

- Cache thuần túy đã được xác định là SAFE_TO_DELETE.
- Một số generated artifacts được xác định là SAFE_TO_REGENERATE nhưng
  chưa được nâng thành SAFE_TO_DELETE_NOW.
- Persistent application/data state được PROTECTED.
- Database migration history được PROTECTED.
- Source backup candidate vẫn REQUIRES_MORE_EVIDENCE.
- Không có source module nào được phê duyệt xóa.
- Không có source code nào được xác định DEAD chỉ dựa trên việc không có
  internal import.
- Repository vẫn clean sau toàn bộ audit.


============================================================
2. SAFE_TO_DELETE_NOW
============================================================

Chỉ áp dụng cho generated cache:

    .hypothesis/
    .pytest_cache/
    .ruff_cache/
    .mypy_cache/
    **/__pycache__/

Classification:

    SAFE_TO_DELETE

Reason:

- Git ignored.
- Generated/cache-only surfaces.
- Có thể regenerate.
- Không phải source code.
- Không phải persistent business/application state.
- Không phải migration history.

IMPORTANT:

SAFE_TO_DELETE là classification trong audit.
Không có deletion nào được thực hiện trong Phase A.


============================================================
3. SAFE_TO_REGENERATE
============================================================

    artifacts/

Classification:

    SAFE_TO_REGENERATE

Qualification:

- Có evidence đây là generated/materialized artifact surface.
- Có source/config/test/Docker references.
- Vì vậy không được mặc định coi toàn bộ contents là disposable.
- Chỉ kết luận rằng artifacts có khả năng được regenerate.
- Chưa nâng classification thành SAFE_TO_DELETE_NOW.


============================================================
4. PROTECTED FILES / DIRECTORIES
============================================================

4.1 Persistent database

    data_quality.db

Classification:

    PROTECTED

Reason:

- Git-tracked.
- Persistent database state.
- Có configuration/application references.
- Không được coi là disposable local cache.


4.2 Chroma persistent state

    chroma/

Classification:

    PROTECTED

Reason:

- Persistent application state.
- Có active implementation/runtime references.
- Git ignored không đồng nghĩa disposable.
- Không được xóa trong Phase A.


4.3 Database migration history

    database/migrations/

    database/migrations/archive/legacy_versions/

Classification:

    PROTECTED

Reason:

- Migration history là schema/database provenance.
- Archive chứa historical migration versions.
- Các migration archive files được Git track.
- Có thể cần cho migration graph, forensic analysis, historical state,
  repair/provisioning reasoning và database contract.
- Không được xóa chỉ vì path chứa "archive", "legacy" hoặc "old".


4.4 Reports/source modules

    reports/

Classification:

    PROTECTED

Reason:

- Đây là source module, không phải cache directory.
- Có active references đã được chứng minh ở các phase trước.


4.5 Tracked audit / architecture / migration evidence

Bao gồm các nhóm tài liệu như:

    ARCHITECTURE_*.md
    MIGRATION_*.md
    PHASE_*.md
    PRODUCTION_*.md
    SCHEMA_*.md
    DATABASE_*.md
    *_REPORT.md

Classification:

    PROTECTED

Reason:

- Là audit/architecture/migration/operational evidence.
- Không được coi là disposable chỉ vì là report/document.


============================================================
5. REQUIRES_MORE_EVIDENCE
============================================================

5.1 Source backup candidate

    application/changesets/changeset_service.py.s18-backup

Classification:

    REQUIRES_MORE_EVIDENCE

Reason:

- Filename cho thấy đây là backup/snapshot.
- Tuy nhiên backup naming không chứng minh file là dead.
- Chưa đủ evidence về:
  - rollback usage
  - historical/forensic usage
  - repair workflow
  - external consumer
  - documented recovery dependency
- Không được xóa/move/rename trong Phase A.


5.2 Data candidates

    raw_fashion_data.csv
    test_products.csv

Classification:

    REQUIRES_MORE_EVIDENCE

Reason:

- Chưa đủ evidence để chứng minh là disposable.
- Có thể là fixture, seed/input data hoặc external workflow input.
- Không được xóa trong Phase A.


============================================================
6. REPOSITORY INTEGRITY
============================================================

Final Git state:

    Branch:
        main

    TRACKED:
        624

    UNTRACKED:
        0

    git status --porcelain=v1:
        CLEAN

Conclusion:

- Audit commands không tạo repository modification.
- Không có file mới/untracked phát sinh.
- Không có source/database/config/migration file nào bị thay đổi.


============================================================
7. PHASE A CLASSIFICATION SUMMARY
============================================================

SAFE_TO_DELETE_NOW:

    .hypothesis/
    .pytest_cache/
    .ruff_cache/
    .mypy_cache/
    **/__pycache__/

SAFE_TO_REGENERATE:

    artifacts/

PROTECTED:

    data_quality.db
    chroma/
    database/migrations/
    database/migrations/archive/legacy_versions/
    reports/
    tracked architecture/audit/migration evidence

REQUIRES_MORE_EVIDENCE:

    application/changesets/changeset_service.py.s18-backup
    raw_fashion_data.csv
    test_products.csv

SAFE_TO_DELETE_SOURCE:

    NONE


============================================================
8. FALSE-POSITIVE RULES CARRIED FORWARD
============================================================

Do NOT classify a file/module as dead merely because:

- không có direct import;
- nằm trong archive/legacy;
- cũ;
- lớn;
- generated;
- Git ignored;
- không được test trực tiếp;
- không được gọi từ current internal path;
- có tên backup/old/deprecated;
- passing tests không chứng minh production usage.

External consumers, dynamic imports, runtime registration, entrypoints,
Docker/Compose, CI/CD, plugins, filesystem references, migration history
và compatibility surfaces phải tiếp tục được xem xét.


============================================================
9. PHASE B HANDOFF
============================================================

Phase B có thể bắt đầu.

Scope chính:

    1. controllers/
    2. views/
    3. ai/
    4. compatibility re-exports:
         api/schemas.py
         models/database.py
         models/domain.py
    5. validators/ vs plugins/
    6. application/changesets/changeset_service.py.s18-backup
    7. duplicate/legacy implementations
    8. dynamic registration
    9. external-consumer risk
    10. test/Docker/CI/runtime references

Known classifications carried forward:

    main.py
        = LEGACY_ACTIVE / COMPATIBILITY

    dashboard.py
        = CURRENT / ACTIVE

    worker.py
        = CURRENT / PRODUCTION ACTIVE

    app/main.py
        = CURRENT

    api/main.py
        = CURRENT

    app/dashboard.py
        = CURRENT

    api/schemas.py
        = COMPATIBILITY

    models/database.py
        = COMPATIBILITY

    models/domain.py
        = COMPATIBILITY

    plugins/
        = CURRENT / ACTIVE

    validators/
        = LEGACY_ACTIVE / FALLBACK

    controllers/
        = UNKNOWN / NO PROVEN INTERNAL CONSUMER

    views/
        = UNKNOWN / NO PROVEN INTERNAL CONSUMER

    ai/
        = UNKNOWN / NO PROVEN INTERNAL CONSUMER


============================================================
10. PHASE A FINAL STATUS
============================================================

PROVEN:

- Cache cleanup candidates identified.
- Persistent database protected.
- Chroma persistent state protected.
- Migration history protected.
- Backup candidate identified.
- Repository integrity preserved.
- No deletion/modification performed.

PARTIALLY_EVIDENCED:

- artifacts/ regeneration/disposability.
- Selected root-level data/report artifacts.

UNKNOWN:

- External/historical consumer role of
  application/changesets/changeset_service.py.s18-backup.
- Exact role of selected CSV/data artifacts.

BLOCKED:

    NONE

NEXT ACTION:

    PROCEED TO PHASE B — SOURCE / MODULE CLEANUP AUDIT


============================================================
FINAL SAFETY STATEMENT
============================================================

PHASE A DOES NOT AUTHORIZE SOURCE CODE DELETION.

SAFE_TO_DELETE_NOW is LIMITED TO GENERATED CACHE SURFACES.

NO SOURCE MODULE IS CURRENTLY APPROVED FOR DELETION.

NO DATABASE, CHROMA STATE, MIGRATION HISTORY, COMPATIBILITY SURFACE,
ENTRYPOINT, PLUGIN, OR LEGACY FALLBACK MAY BE REMOVED WITHOUT
ADDITIONAL EVIDENCE AND EXPLICIT AUTHORIZATION.


============================================================
END OF PHASE A HANDOFF
============================================================

==================================================
PHASE
==================================================

PHASE B — CONFIRMED DEAD CODE AUDIT

OBJECTIVE:
Determine whether suspected legacy/scaffold/compatibility source code is actually dead, externally consumed, dynamically loaded, runtime-required, duplicated, or still active.

==================================================
PRIMARY TARGETS
==================================================

At minimum inspect:

- controllers/
- ai/
- views/
- root compatibility wrappers
- compatibility re-exports
- suspicious legacy modules
- apparently unused services
- apparently unused validators
- apparently unused rule-engine modules
- apparently unused repositories
- apparently unused agents
- other candidates discovered from evidence

==================================================
CRITICAL RULE
==================================================

Do NOT classify code as DEAD solely because direct static imports are zero.

Check:

1. Static imports
2. Reverse imports
3. Dynamic imports
4. importlib
5. __import__
6. getattr/reflection
7. registries
8. dependency injection
9. FastAPI route registration
10. Streamlit references
11. worker references
12. configuration
13. environment variables
14. Docker/Compose
15. CI/CD
16. filesystem/path references
17. templates
18. tests
19. documentation
20. entrypoints
21. plugin systems
22. external-consumer possibility

==================================================
CLASSIFICATION
==================================================

Each candidate:

DEAD
LEGACY_ACTIVE
COMPATIBILITY
HISTORICAL
DUPLICATED
CURRENT
UNKNOWN

Also:

INTERNAL_USAGE =
DYNAMIC_USAGE =
RUNTIME_USAGE =
EXTERNAL_USAGE =
CONFIDENCE = HIGH / MEDIUM / LOW

==================================================
OUTPUT
==================================================

1. EXECUTIVE SUMMARY

2. CANDIDATE INVENTORY

3. MODULE-BY-MODULE AUDIT

4. DEAD-CODE EVIDENCE

5. LEGACY_ACTIVE EVIDENCE

6. COMPATIBILITY SURFACES

7. EXTERNAL-CONSUMER UNKNOWNs

8. SAFE_TO_DELETE

9. NOT_SAFE_TO_DELETE

10. REQUIRES_MORE_EVIDENCE

11. REQUIRES_RUNTIME_VERIFICATION

12. REQUIRES_EXPLICIT_AUTHORIZATION

13. FINDINGS THAT AFFECT PHASE C

==================================================
STATE CONSISTENCY
==================================================

Compare against:

- MASTER CONTEXT
- LATEST CONSOLIDATED STATE
- PHASE A HANDOFF

If contradictory evidence exists:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Never silently overwrite previous classifications.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = B
PHASE_NAME = CONFIRMED_DEAD_CODE
PHASE_STATUS =

CODE_CLEANUP_STATUS =

SAFE_TO_DELETE_NOW =
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

CONFIRMED_CURRENT =
CONFIRMED_COMPATIBILITY =
CONFIRMED_LEGACY_ACTIVE =
CONFIRMED_HISTORICAL =
CONFIRMED_DUPLICATED =
CONFIRMED_DEAD =
UNKNOWN_CANDIDATES =

SAFE_TO_DELETE_NOW =
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

Create a self-contained state for Phase C.

Preserve all still-valid findings from previous phases.

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

SAFE_TO_DELETE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

KNOWN_ARCHITECTURAL_DEBT =
KNOWN_RUNTIME_RISKS =
KNOWN_PRODUCT_GAPS =
UNKNOWN =
BLOCKED =