PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Software Architect + Dead-Code / Dependency Auditor.

READ-ONLY ONLY.
DO NOT DELETE OR MODIFY CODE.

==================================================
MASTER CONTEXT
==================================================

[PASTE MASTER CONTEXT HERE]

==================================================
LATEST CONSOLIDATED STATE
==================================================

[PASTE UPDATED CONSOLIDATED PROJECT STATE FROM PHASE A]

==================================================
PHASE A HANDOFF
==================================================

[PASTE PHASE A HANDOFF]

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