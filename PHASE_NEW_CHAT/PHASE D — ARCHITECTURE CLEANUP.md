[PASTE MASTER CONTEXT HERE]

PHASE:
PHASE D — ARCHITECTURE CLEANUP AUDIT AND PLAN

OBJECTIVE:
Based on Phase B and Phase C evidence, determine what architectural cleanup is justified.

IMPORTANT:
Do not redesign the system from scratch.
Do not assume a clean-layer architecture is automatically better.
Preserve working behavior and compatibility unless explicitly authorized otherwise.

CURRENT ARCHITECTURE APPEARS HYBRID:
api
→ application
→ domain
→ repositories/infrastructure
with additional:
services
execution
capabilities
agents
rule_engine
validators
plugins

KNOWN DEPENDENCY PATTERNS:
- application → services
- services → application
- application → repositories
- services → repositories
- repositories → infrastructure
- infrastructure → application exists in some paths
- application → infrastructure exists
- execution → infrastructure
- application → execution
- plugins → rule_engine/domain/validators
- agents → domain/rule_engine
- API → application/domain/repositories/services/infrastructure

AUDIT:
1. Define actual architectural layers.
2. Define actual dependency directions.
3. Identify intentional exceptions.
4. Identify accidental coupling.
5. Identify transitional architecture.
6. Identify compatibility architecture.
7. Identify domain leakage.
8. Identify infrastructure leakage.
9. Identify service/application overlap.
10. Identify composition-root responsibilities.
11. Identify runtime registration boundaries.
12. Identify plugin boundaries.
13. Identify execution/worker boundaries.
14. Identify persistence boundaries.

DO NOT change anything.

OUTPUT:

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
Describe only the target state justified by evidence.

11. MIGRATION ORDER
Must be incremental.

For each migration:
- exact modules
- prerequisite
- dependency
- risk
- expected behavior impact
- tests
- rollback
- stop condition

12. FINAL STATUS
ARCHITECTURE_STATUS =