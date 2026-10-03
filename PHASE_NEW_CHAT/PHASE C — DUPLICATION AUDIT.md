[PASTE MASTER CONTEXT HERE]

PHASE:
PHASE C — DUPLICATION AND RESPONSIBILITY OVERLAP AUDIT

OBJECTIVE:
Identify duplicated business logic, overlapping responsibilities, parallel implementations, compatibility layers, and competing abstractions.

READ-ONLY ONLY.
DO NOT REFACTOR.

FOCUS AREAS:
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
application <-> services is bidirectional.
Do not automatically label this as wrong; determine actual responsibility and runtime dependency.

LOOK FOR:
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
- old/new implementations coexisting
- compatibility wrappers
- parallel service implementations
- duplicated schemas/models
- duplicated API behavior

FOR EACH OVERLAP:
- implementation A
- implementation B
- responsibility
- callers
- runtime usage
- tests
- differences
- compatibility reason
- whether one can replace the other
- evidence level

CLASSIFY:
CURRENT_UNIQUE
CURRENT_DUPLICATED
LEGACY_ACTIVE
COMPATIBILITY
HISTORICAL
UNKNOWN

DO NOT recommend deletion merely because two implementations look similar.

OUTPUT:

1. EXECUTIVE SUMMARY

2. DUPLICATION MATRIX

3. RESPONSIBILITY MAP

4. APPLICATION VS SERVICES ANALYSIS

5. DOMAIN VS SERVICE LOGIC ANALYSIS

6. RULE_ENGINE VS VALIDATORS ANALYSIS

7. AGENTS VS AI/COPILOT ANALYSIS

8. REPOSITORY/PERSISTENCE OVERLAPS

9. API/SERVICE OVERLAPS

10. SAFE CONSOLIDATION CANDIDATES

11. NOT_SAFE_TO_CONSOLIDATE

12. REQUIRES_RUNTIME_VERIFICATION

13. PHASE C ROADMAP
For each item:
scope
modules
reason
dependencies
risk
behavior impact
tests
rollback
stop condition

14. FINAL STATUS
CODE_CLEANUP_STATUS =
ARCHITECTURE_STATUS =