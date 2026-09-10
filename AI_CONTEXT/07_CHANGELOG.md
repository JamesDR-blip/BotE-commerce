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

---

## ADR-005

**Decision:**
Introduce semantic rule retrieval behind a framework-independent `RuleRetriever` domain port, with Chroma isolated in the infrastructure layer.

**Reason:**
1. Enable context-aware rule discovery beyond static category lookup.
2. Keep Chroma, embeddings, and vector-store concerns outside the domain layer.
3. Preserve the existing deterministic `RuleRetrieverAgent.retrieve(category)` contract for executable validation.
4. Allow semantic retrieval to return typed, non-executable `SemanticRulePack` results.

**Status:**
Accepted and Implemented.

---

## ADR-006

**Decision:**
Keep semantic rule indexing explicit rather than synchronizing automatically during application startup.

**Reason:**
1. Avoid embedding-model loading and vector-store synchronization as startup side effects.
2. Keep YAML rule definitions as the authoritative source for parsing and versioning.
3. Make index synchronization an explicit application operation.
4. Allow stale vector-index entries to be removed during synchronization.

**Status:**
Accepted and Implemented.

---

## ADR-007

**Decision:**
Distinguish descriptive rule knowledge from executable validation rules in the semantic index.

**Reason:**
Semantic retrieval may return business guidance or descriptive rules that are useful for recommendation but must never become executable validation logic implicitly. Executable validation remains constrained to registered declarative primitives.

**Status:**
Accepted and Implemented.
