[PASTE MASTER CONTEXT HERE]

PHASE:
PHASE A — SAFE FILE CLEANUP AUDIT

OBJECTIVE:
Audit generated/local/artifact files and determine which files are genuinely disposable without affecting runtime, persistence, tests, deployment, documentation, or external workflows.

DO NOT MODIFY ANYTHING.

SCOPE:
- .hypothesis/
- .pytest_cache/
- .ruff_cache/
- .mypy_cache/
- __pycache__/
- pytest temporary directories
- artifacts/
- reports/
- generated test artifacts
- local databases
- Chroma state
- logs
- generated reports
- temporary files
- build/cache outputs
- any suspicious root-level artifacts

IMPORTANT:
Do not assume a file is disposable because:
- it looks generated
- it is old
- it is not imported
- it is not source code
- it is large
- it is ignored by Git

CHECK:
1. Git tracked/untracked/ignored status where possible.
2. References from source code.
3. References from tests.
4. References from Docker/Compose.
5. References from CI/CD.
6. References from scripts.
7. References from configuration.
8. Runtime persistence role.
9. Whether it is reproducible.
10. Whether deleting it changes behavior.
11. Whether it contains user/business data.
12. Whether it is required for local development.
13. Whether it is required for deployment.
14. Whether it is evidence/audit output that should be retained.

CLASSIFY EACH TARGET:
- SAFE_TO_DELETE
- SAFE_TO_REGENERATE
- PROTECTED
- REQUIRES_MORE_EVIDENCE
- UNKNOWN

DO NOT DELETE ANYTHING.

OUTPUT:

1. EXECUTIVE SUMMARY

2. FILE CLEANUP MATRIX
Columns:
PATH
TYPE
GIT_STATUS
RUNTIME_REFERENCE
TEST_REFERENCE
PERSISTENCE_ROLE
REGENERABLE
RISK
CLASSIFICATION
EVIDENCE

3. SAFE_TO_DELETE_NOW
Must be empty unless deletion is strongly proven safe.

4. SAFE_TO_REGENERATE

5. PROTECTED_FILES

6. REQUIRES_MORE_EVIDENCE

7. REQUIRES_RUNTIME_VERIFICATION

8. PHASE A RECOMMENDATION
For every proposed cleanup:
- exact path
- why safe
- what depends on it
- expected impact
- rollback
- validation required

9. FINAL STATUS
FILE_CLEANUP_STATUS =
SAFE_TO_DELETE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =