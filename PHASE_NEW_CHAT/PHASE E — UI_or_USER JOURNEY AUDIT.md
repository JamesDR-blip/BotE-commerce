PROJECT:
Autonomous E-commerce Data Operations Platform

ROLE:
Senior Product Architect + UX Auditor + Technical Product Auditor.

READ-ONLY ONLY.
DO NOT MODIFY UI OR BACKEND.

==================================================
MASTER CONTEXT
==================================================

[PASTE MASTER CONTEXT HERE]

==================================================
LATEST CONSOLIDATED STATE
==================================================

[PASTE UPDATED CONSOLIDATED STATE FROM PHASE D]

==================================================
PHASE D HANDOFF
==================================================

[PASTE PHASE D HANDOFF]

==================================================
PHASE
==================================================

PHASE E — ACTUAL UI / USER JOURNEY AUDIT

OBJECTIVE:
Determine what a real user can actually accomplish through the current product UI, not merely what exists in backend code.

==================================================
KNOWN UI
==================================================

- app/dashboard.py = current Streamlit dashboard candidate
- dashboard.py = compatibility launcher
- app/api_client.py exists
- FastAPI backend exists

Do not assume backend capability is user-accessible.

==================================================
USER JOURNEY
==================================================

Audit:

1. Entry
2. Authentication
3. Authorization
4. Organization
5. Workspace
6. Project
7. Dataset
8. Data upload/import
9. Mapping
10. Validation
11. Rules
12. Sync
13. Workflow authoring
14. Workflow execution
15. Queue/execution status
16. Quality results
17. Reports
18. Changesets
19. Approval
20. Risk
21. Audit
22. Lineage
23. Semantic search
24. AI/Copilot
25. Monitoring
26. Configuration
27. Integrations
28. Export

==================================================
FOR EVERY CAPABILITY
==================================================

Determine:

BACKEND =
API =
UI =
UI_ROUTE_OR_CONTROL =
TESTS =
DOCUMENTATION =
DISCOVERABLE =
USER_CAN_COMPLETE =
ERROR_STATE =
LOADING_STATE =
EMPTY_STATE =
PERMISSION_BEHAVIOR =
TENANT_CONTEXT =
RESULT_VISIBILITY =
RECOVERY_PATH =

STATUS:

PROVEN
PARTIALLY_EVIDENCED
UNKNOWN
BLOCKED
NOT_APPLICABLE

==================================================
OUTPUT
==================================================

1. ACTUAL USER JOURNEY

2. SCREEN / PAGE MAP

3. CAPABILITY MATRIX

Columns:

CAPABILITY
BACKEND
API
UI
TESTS
DOCUMENTATION
USER_ACCESSIBLE
STATUS

Minimum capabilities:

authentication
authorization
organizations
workspaces
projects
datasets
channels
mappings
sync
workflow
queued execution
validation
rules
semantic search
AI/Copilot
changesets
approvals
risk
audit
lineage
reports
exports
monitoring
configuration
integrations

4. USER JOURNEY GAPS

5. UI GAPS

6. BACKEND-ONLY CAPABILITIES

7. PARTIAL CAPABILITIES

8. BLOCKED JOURNEYS

9. MUST_FIX_BEFORE_FIRST_CUSTOMER

10. SHOULD_FIX_BEFORE_PAID_SCALE

11. NICE_TO_HAVE

12. UNKNOWN

13. FINDINGS THAT AFFECT PHASE F

==================================================
STATE CONSISTENCY
==================================================

Compare against previous consolidated state and Phase D.

If new evidence contradicts prior findings:

STATE_CHANGE =
OLD =
NEW =
REASON =
EVIDENCE =
IMPACT_ON_PREVIOUS_PHASES =

Do not silently overwrite previous state.

==================================================
MANDATORY FINAL OUTPUT
==================================================

A. FINAL STATUS

PHASE_ID = E
PHASE_NAME = UI_AND_USER_JOURNEY
PHASE_STATUS =

UI_STATUS =
USER_FLOW_STATUS =
CAPABILITY_STATUS =

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

ACTUAL_USER_JOURNEY =
UI_SURFACES =
BACKEND_ONLY_CAPABILITIES =
PARTIAL_CAPABILITIES =
BLOCKED_JOURNEYS =

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

NEW_EVIDENCE_REQUIRED_FOR_NEXT_PHASE =
INPUT_REQUIRED_BY_NEXT_PHASE =
RECOMMENDED_NEXT_ACTION =

STATE_CHANGE =

C. UPDATED CONSOLIDATED PROJECT STATE

Create self-contained state for Phase F.

Preserve all previous findings.

Update:

UI_STATUS =
USER_FLOW_STATUS =
CAPABILITY_STATUS =

CURRENT_USER_JOURNEY =
CURRENT_UI_SURFACES =
BACKEND_ONLY_CAPABILITIES =
USER_ACCESSIBLE_CAPABILITIES =
BLOCKED_CAPABILITIES =

MUST_FIX_BEFORE_FIRST_CUSTOMER =
SHOULD_FIX_BEFORE_PAID_SCALE =
NICE_TO_HAVE =

Also preserve architecture, cleanup, runtime, security and commercial unknowns.