PROJECT: Autonomous E-commerce Data Operations Platform

ROLE:
Act as a Senior Software Architect, Repository Auditor, Product Architect, and Implementation Planner.

PHASE G — MASTER CLEANUP AND PRODUCT ROADMAP

MODE: READ-ONLY PLANNING.
DO NOT MODIFY THE REPOSITORY.
DO NOT DELETE OR EDIT FILES.
DO NOT IMPLEMENT CODE.
DO NOT CHANGE DATABASE, MIGRATIONS, DEPENDENCIES, CONFIGURATION, DOCKER, API, OR UI.

==================================================
1. MASTER CONTEXT
==================================================

[PASTE THE APPROVED MASTER CONTEXT HERE]

==================================================
2. FINAL CONSOLIDATED PROJECT STATE FROM PHASE F
==================================================

[PASTE THE COMPLETE UPDATED CONSOLIDATED PROJECT STATE FROM PHASE F]

==================================================
3. PHASE F HANDOFF
==================================================

[PASTE THE COMPLETE PHASE F HANDOFF]

==================================================
4. UNRESOLVED STATE CHANGES FROM PHASES A-E
==================================================

[PASTE ONLY STATE_CHANGE RECORDS THAT ARE NOT ALREADY REFLECTED IN THE CONSOLIDATED STATE. IF NONE, WRITE NONE.]

==================================================
OBJECTIVE
==================================================

Synthesize the evidence from Phases A-F into one coherent, evidence-driven roadmap.

Do not repeat the full repository audit.
Do not invent missing evidence.
Do not silently resolve contradictions.
Do not assume that every identified issue must be fixed.
Do not equate legacy code with dead code.
Do not equate passing tests with production readiness.
Do not approve deletion merely because code appears unused.
Do not convert recommendations into authorization.

If an input or prior-phase finding is missing, mark it UNKNOWN or NEEDS_INPUT.
If two findings conflict, create a STATE_RECONCILIATION item showing both findings, evidence, and the verification needed. Do not arbitrarily choose one.

==================================================
ROADMAP PHASES
==================================================

Create a roadmap with these workstreams:

PHASE A — Safe file cleanup
PHASE B — Confirmed dead-code removal
PHASE C — Duplication cleanup
PHASE D — Architecture cleanup
PHASE E — UI/UX cleanup
PHASE F — Commercial readiness

These are roadmap workstreams, not permission to execute the earlier audit phases again or to modify the repository.

For every proposed task provide:

TASK_ID
ROADMAP_PHASE
TITLE
TYPE
PRIORITY_RATIONALE
EVIDENCE
EVIDENCE_LEVEL
CURRENT_STATE
TARGET_STATE
EXACT_FILES_OR_MODULES
SCOPE_BOUNDARY
DEPENDENCIES
BLOCKERS
RISK
EXPECTED_BEHAVIOR_IMPACT
DB_IMPACT
API_IMPACT
UI_IMPACT
SECURITY_IMPACT
TESTS_REQUIRED
VALIDATION_STEPS
ROLLBACK
STOP_CONDITION
AUTHORIZATION_REQUIRED
IMPLEMENTATION_READINESS

Allowed IMPLEMENTATION_READINESS values:
READY_FOR_IMPLEMENTATION_REVIEW
NEEDS_MORE_EVIDENCE
NEEDS_RUNTIME_VERIFICATION
BLOCKED
NOT_RECOMMENDED

READY_FOR_IMPLEMENTATION_REVIEW does not mean implementation is authorized.

Do not combine unrelated changes into a single task.
Do not create vague tasks such as "refactor the entire project".
Only name exact files or modules when supported by evidence. Otherwise explicitly state that exact scope must be confirmed.

==================================================
REQUIRED ANALYSIS
==================================================

1. EXECUTIVE SUMMARY

2. CURRENT PROJECT MAP

Summarize the established modules and their roles. Distinguish evidence from inference.

3. CURRENT RUNTIME MAP

Summarize API, dashboard/UI, worker, persistence, queues, plugins, and deployment surfaces. Separate statically evidenced behavior from behavior requiring runtime verification.

4. CONSOLIDATED AUDIT FINDINGS

Summarize file cleanup, dead-code candidates, duplication, architecture, UI/user journey, and commercial readiness.

5. STATE RECONCILIATION

List unresolved contradictions or changes between phases. Do not silently overwrite prior decisions.

6. ROADMAP TASK INVENTORY

Provide a master task table with:
TASK_ID, PHASE, TITLE, READINESS, DEPENDENCIES, AUTHORIZATION_REQUIRED.

7. DETAILED ROADMAP

For every task, include all required task fields listed above.

8. SAFE FILE CLEANUP

Separate:
- proven disposable files
- regenerable files
- protected persistent data
- unresolved candidates

Never recommend deleting persistent data without explicit evidence and authorization.

9. CONFIRMED DEAD-CODE REMOVAL

Only propose source deletion where evidence is sufficient. If none qualifies, explicitly state SAFE_TO_DELETE_NOW = NONE.

10. DUPLICATION CLEANUP

Describe specific responsibility overlaps and the smallest safe consolidation units. Do not assume similar-looking implementations are interchangeable.

11. ARCHITECTURE CLEANUP

Use the actual dependency evidence. Preserve compatibility unless removal is explicitly approved. Prefer incremental migration over rewrite.

12. UI/UX ROADMAP

Prioritize complete, user-accessible journeys and gaps supported by Phase E evidence. Do not assume backend features are exposed through the UI.

13. COMMERCIAL READINESS ROADMAP

Use the Phase F categories:
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

Preserve the source status for every category:
PROVEN, PARTIALLY_EVIDENCED, UNKNOWN, BLOCKED, or NOT_APPLICABLE.

Do not manufacture scores or readiness claims.

14. MUST FIX BEFORE FIRST CUSTOMER

Only include evidence-supported items. Distinguish confirmed blockers from prudent recommendations and unverified risks.

15. SHOULD FIX BEFORE PAID SCALE

16. NICE TO HAVE

17. UNKNOWN AND BLOCKED

For each item, state the evidence or action needed to unblock it.

18. DEPENDENCY-ORDERED EXECUTION PLAN

Group tasks into small, verifiable batches. Explain why the order matters. Do not use arbitrary priority rankings without rationale.

19. VALIDATION STRATEGY

Use the established test baseline as historical evidence only:
994 passed, 0 failed, 0 errors, 0 skipped, 0 warnings.

Do not claim the current repository still passes this baseline unless tests are rerun in the implementation environment.

Define targeted tests, integration tests, regression gates, runtime verification, and deployment verification appropriate to each task.

20. ROLLBACK AND STOP RULES

Define when to stop, restore the previous state, or return to audit because assumptions were invalidated.

==================================================
IMPLEMENTATION GATE INPUT
==================================================

Create a proposed inventory for the next phase, H — Implementation Gate.

For every candidate, include:
CHANGE_ID
TITLE
SOURCE_FINDING
EXACT_SCOPE
DEPENDENCIES
RISK
VALIDATION
ROLLBACK
AUTHORIZATION_REQUIRED
STATUS

Allowed statuses:
READY_FOR_IMPLEMENTATION_REVIEW
NEEDS_MORE_EVIDENCE
NEEDS_RUNTIME_VERIFICATION
BLOCKED
NOT_APPROVED

Do not mark a change as approved merely because it is low-risk.
Do not infer user authorization.
Do not implement anything.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

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
SAFE_TO_REGENERATE =
SAFE_TO_CONSOLIDATE_NOW =
REQUIRES_MORE_EVIDENCE =
REQUIRES_RUNTIME_VERIFICATION =
REQUIRES_EXPLICIT_AUTHORIZATION =

PROVEN =
PARTIALLY_EVIDENCED =
UNKNOWN =
BLOCKED =

B. PHASE G HANDOFF

PHASE_ID = G
PHASE_NAME = MASTER_CLEANUP_AND_PRODUCT_ROADMAP
PHASE_STATUS =

ROADMAP_TASKS =
IMPLEMENTATION_CANDIDATES =
BLOCKED_TASKS =
UNKNOWN_TASKS =
STATE_RECONCILIATION_ITEMS =

FIRST_RECOMMENDED_TASK =
FIRST_TASK_PREREQUISITES =
REQUIRED_AUTHORIZATIONS =
NEXT_PHASE = H — IMPLEMENTATION GATE

C. FINAL CONSOLIDATED PROJECT STATE

Produce a self-contained, updated project state for Phase H.

Preserve all valid Phase F findings. Add the roadmap and task IDs, but do not change evidence classifications without documenting STATE_CHANGE.

Include:
- project and architecture status
- code/file cleanup status
- UI, user-flow, and capability status
- commercial and production readiness
- current, compatibility, legacy/investigation, historical, duplicated, and confirmed-dead classifications
- protected data
- architectural debt
- runtime, security, and deployment risks
- current product proposition, target user, core workflow, and customer value
- must-fix-before-first-customer
- should-fix-before-paid-scale
- safe-to-delete and safe-to-consolidate candidates
- unresolved evidence and runtime verification
- explicit authorization requirements
- dependency-ordered roadmap task inventory
- implementation candidates and blocked items
- final recommended next action

The final state must be usable in a new chat without access to this conversation.

END OF PHASE G PROMPT.