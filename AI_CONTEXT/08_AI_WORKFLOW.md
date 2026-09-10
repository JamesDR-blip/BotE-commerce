# AI WORKFLOW

## STEP 1 — CONTEXT

Before working:
1. Read `AI_CONTEXT/`.
2. Read current sprint specification.
3. Read `HANDOFF/`.
4. Inspect relevant source code.

Never assume previous conversation context is authoritative.
**Repository state is authoritative.**

---

## STEP 2 — UNDERSTAND

Determine:
- current architecture
- current sprint
- completed functionality
- existing abstractions
- relevant tests
- database state
- constraints
- known risks

---

## STEP 3 — PLAN

Before implementation:
- identify reusable components
- identify required changes
- identify architectural impact
- identify migration impact
- identify security impact
- identify testing strategy

Do not redesign the system unnecessarily.

---

## STEP 4 — IMPLEMENT

Implement the smallest coherent change.

Prefer:
`existing abstraction` > `extend existing abstraction` > `new abstraction`

Do not bypass architectural boundaries.

---

## STEP 5 — VERIFY

Run:
- unit tests (`python -m pytest`)
- integration tests where relevant
- regression tests

Inspect changed files.
Check security implications.
Check migration consistency.

---

## STEP 6 — DOCUMENT

Update:
- `PROJECT_STATE`
- `CHANGELOG` when architecture decisions change
- sprint status
- handoff

---

## STEP 7 — HANDOFF

Always produce:
- completed work
- changed files
- tests
- migrations
- architectural decisions
- known issues
- next action

