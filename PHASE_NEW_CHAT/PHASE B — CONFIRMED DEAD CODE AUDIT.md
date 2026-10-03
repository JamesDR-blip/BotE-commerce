[PASTE MASTER CONTEXT HERE]

PHASE:
PHASE B — CONFIRMED DEAD CODE AUDIT

OBJECTIVE:
Determine whether suspected legacy/scaffold/compatibility source code is actually dead, externally consumed, dynamically loaded, or still required.

READ-ONLY ONLY.
DO NOT DELETE OR MODIFY CODE.

PRIMARY TARGETS:
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

CRITICAL RULE:
Do NOT classify code as DEAD solely because direct static imports are zero.

For each candidate inspect:

1. Static imports
2. Reverse imports
3. Dynamic imports
4. importlib
5. __import__
6. getattr/reflection
7. registry systems
8. plugin registration
9. dependency injection
10. FastAPI route registration
11. Streamlit references
12. worker references
13. configuration references
14. environment-variable references
15. Docker/Compose references
16. CI/CD references
17. filesystem/path references
18. templates
19. tests
20. documentation that describes current runtime behavior
21. entrypoint behavior
22. possible external consumer risk

CLASSIFICATION:
For every module/file use exactly one primary classification:
- DEAD
- LEGACY_ACTIVE
- COMPATIBILITY
- HISTORICAL
- DUPLICATED
- CURRENT
- UNKNOWN

Also provide:
INTERNAL_USAGE =
DYNAMIC_USAGE =
RUNTIME_USAGE =
EXTERNAL_USAGE =
CONFIDENCE = HIGH / MEDIUM / LOW

DO NOT infer external usage from absence of evidence.

OUTPUT:

1. EXECUTIVE SUMMARY

2. CANDIDATE INVENTORY

3. MODULE-BY-MODULE AUDIT

4. DEAD-CODE EVIDENCE

5. LEGACY_ACTIVE EVIDENCE

6. COMPATIBILITY SURFACES

7. EXTERNAL-CONSUMER UNKNOWNs

8. SAFE_TO_DELETE
Only list items where deletion is strongly proven safe.

9. NOT_SAFE_TO_DELETE

10. REQUIRED FOLLOW-UP VERIFICATION

11. PROPOSED PHASE B CLEANUP PLAN
No implementation.

Each proposed removal must include:
- exact path
- evidence
- dependencies
- risk
- expected behavior impact
- tests required
- rollback
- stop condition

12. FINAL STATUS
CODE_CLEANUP_STATUS =
SAFE_TO_DELETE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =