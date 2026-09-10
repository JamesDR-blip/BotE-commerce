# CHANGELOG

## ADR-001

**Decision:**
Use Clean Architecture + Domain-Driven Design (DDD).

**Reason:**
Prevent framework and infrastructure coupling. Keep business rules and domain logic pure and independent from web frameworks (FastAPI/Streamlit) and ORMs (SQLAlchemy).

**Status:**
Accepted.

---

## ADR-002

**Decision:**
ChangeSet is the only production mutation boundary.

**Reason:**
Required for rollback, audit trails, data lineage, and human-in-the-loop approval gates.

**Status:**
Accepted.

---

## ADR-003

**Decision:**
Risk and Confidence are modeled as separate concepts.

**Reason:**
A highly confident automated action can still carry a high blast radius or business risk. Decoupling them allows nuanced approval policies.

**Status:**
Accepted.

---

## ADR-004

**Decision:**
Formalize package layering into `domain/`, `application/`, `execution/`, and `infrastructure/`, and extract domain serialization helpers.

**Reason:**
1. Group use-case services under `application/` (`workspace`, `datasets`, `workflows`, `quality`).
2. Centralize workflow runtime, state transitions, and capability dispatch under `execution/`.
3. Isolate caching behind an `application.cache.Cache` protocol with an infrastructure `TTLCache` implementation.
4. Provide pure domain serialization for `ExecutionPlan` and `WorkflowRequirement` under `domain/serialization/`.

**Status:**
Accepted and Implemented.
