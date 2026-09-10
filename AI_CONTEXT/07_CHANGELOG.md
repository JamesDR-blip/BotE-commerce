\# CHANGELOG



\## ADR-001



Decision:

Use Clean Architecture + DDD.



Reason:

Prevent framework and infrastructure coupling.



Status:

Accepted.



\---



\## ADR-002



Decision:

ChangeSet is the only production mutation boundary.



Reason:

Required for rollback, audit, lineage and approval.



Status:

Accepted.



\---



\## ADR-003



Decision:

Risk and Confidence are separate concepts.



Reason:

A highly confident action can still be high risk.



Status:

Accepted.

