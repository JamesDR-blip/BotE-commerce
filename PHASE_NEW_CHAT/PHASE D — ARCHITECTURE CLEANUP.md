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

[PASTE MASTER CONTEXT HERE]

==================================================
LATEST CONSOLIDATED STATE
==================================================

[PASTE UPDATED CONSOLIDATED STATE FROM PHASE C]

==================================================
PHASE C HANDOFF
==================================================

[PASTE PHASE C HANDOFF]

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