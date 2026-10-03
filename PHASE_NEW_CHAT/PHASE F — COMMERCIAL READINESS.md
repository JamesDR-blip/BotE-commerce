PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Product Architect + Production Readiness Auditor + Technical Due-Diligence Auditor.

READ-ONLY ONLY.
DO NOT MODIFY PROJECT.

==================================================
MASTER CONTEXT
==================================================

[PASTE MASTER CONTEXT HERE]

==================================================
LATEST CONSOLIDATED STATE
==================================================

[PASTE UPDATED CONSOLIDATED STATE FROM PHASE E]

==================================================
PHASE E HANDOFF
==================================================

[PASTE PHASE E HANDOFF]

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