PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Software Architect specializing in responsibility boundaries, duplication analysis, and incremental modernization.

READ-ONLY ONLY.
DO NOT REFACTOR.

==================================================
MASTER CONTEXT
==================================================

[PASTE MASTER CONTEXT HERE]

==================================================
LATEST CONSOLIDATED STATE
==================================================

[PASTE UPDATED CONSOLIDATED STATE FROM PHASE B]

==================================================
PHASE B HANDOFF
==================================================

[PASTE PHASE B HANDOFF]

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