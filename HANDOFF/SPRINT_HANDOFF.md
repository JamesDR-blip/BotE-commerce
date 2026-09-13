# S17 Sprint Handoff

## Status

S17 — Shadow Mode & Simulation: COMPLETE.

The implementation is verified by the full regression suite and preserves the existing Clean Architecture + DDD boundaries. The simulation path is isolated from production mutation.

## Objective

Provide a safe dry-run workflow execution path that can verify workflow behavior, outputs, and tabular diffs without creating production executions, persisting traces, writing dataset storage, or creating ChangeSets.

## Completed Work

### Domain

- Added `SimulationResult`.
- Added `DiffPreview`.
- Added `TabularDiff`.
- Added `RowDiff`.
- Added bounded diff metadata including row counts, column changes, changed rows, and truncation state.

### Execution

- Added `ShadowExecutionRunner`.
- Reused the existing `CapabilityExecutionService` and capability registry.
- Added isolated in-memory simulation.
- Added read-only streaming simulation.
- Added bounded-memory diff accumulation.
- Added deep isolation of DataFrame, Series, and mutable auxiliary inputs.
- Added failure capture into `SimulationResult` without persisting production execution state.

### Application

- Added `SimulationService`.
- Added owner-scoped workflow resolution.
- Added owner-scoped optional dataset resolution.
- Added workflow/dataset project-scope validation.
- Reused the active workflow-version and plan deserialization path.
- Preserved the existing production workflow execution service boundary.

### API

- Added `POST /workflows/{workflow_id}/simulate`.
- Added simulation response schemas.
- Added recursive conversion of DataFrame/Series outputs for API responses.
- Added project-scope error handling.
- Added API coverage proving simulation does not persist production executions.

### Streaming

- Simulation reads datasets through `DatasetStorage.open()` only.
- Streaming uses the existing bounded `StreamingTabularReader`.
- No simulation path calls dataset save/write methods.
- Diff accumulation remains bounded by `max_diff_rows`.
- Every external input is isolated before streaming execution to prevent mutable-input leakage.

## Safety / Security

- `WorkflowEngine` production execution path was not changed.
- Simulation does not create or persist `WorkflowExecution` records.
- Simulation does not persist execution traces.
- Simulation does not write dataset storage.
- Simulation does not create ChangeSets.
- Simulation does not mutate production state.
- S16 Risk & Approval boundaries remain intact.
- Simulation does not bypass production approval controls.
- No `eval`, `exec`, unsafe YAML loading, or arbitrary dynamic LLM execution was introduced.
- No raw production mutation mechanism was added to the shadow runner.
- Existing synchronous production workflow behavior remains backward compatible.

## Architecture Decisions

1. Keep simulation result contracts in the framework-independent domain layer.
2. Keep simulation orchestration in the application and execution layers.
3. Reuse `CapabilityExecutionService` rather than introducing a second capability execution engine.
4. Keep dataset storage access read-only during simulation.
5. Keep production `WorkflowEngine` unchanged.
6. Keep simulation independent from production execution persistence and trace persistence.
7. Use bounded-memory accumulation for streaming diffs rather than materializing the complete dataset.
8. Preserve S16 risk and approval as the production safety boundary.
9. Defer production mutation, immutable ChangeSets, and rollback semantics to S18.

## Database / Migrations

- S17 introduced no database schema changes.
- No Alembic migration was required.
- Existing repository Alembic head remains `20230912_04`.
- Local database revision remains `c13a7e91d204`.
- Local database is not yet synchronized with repository head.
- Existing clean-from-zero Alembic baseline/bootstrap limitation remains known.

## Verification

- Full regression: `546 passed`.
- Full suite runtime: approximately `25.01 seconds`.
- 1 existing Starlette/AnyIO TestClient deprecation warning remains.
- `git diff --check` reports no whitespace errors; Git reports existing Windows LF/CRLF normalization warnings for modified Markdown files.
- Focused S17 simulation, service, streaming, and workflow regression coverage passes.
- Regression coverage includes mutable auxiliary-input isolation.

## Files Added by S17

- `application/workflows/simulation_service.py`
- `domain/simulation.py`
- `execution/shadow_execution_runner.py`
- `tests/test_shadow_execution_runner.py`
- `tests/test_simulation_service.py`

## Files Modified by S17

- `api/dependencies.py`
- `api/main.py`
- `api/routes/workflows.py`
- `schemas/responses.py`
- `services/container.py`
- `tests/test_api_workflow_execution.py`

## Documentation Updated

- `AI_CONTEXT/05_ROADMAP.md`
- `AI_CONTEXT/06_PROJECT_STATE.md`
- `AI_CONTEXT/07_CHANGELOG.md`
- `SPRINTS/README.md`
- `HANDOFF/CURRENT_STATE.md`
- `HANDOFF/SPRINT_HANDOFF.md`

## Known Issues / Limitations

- Streaming row diffs currently use positional row alignment rather than business-key matching.
- Simulation diff preview is bounded by `max_diff_rows`; the API currently uses the runner default.
- Simulation plan deserialization is currently local to `SimulationService`.
- Local Alembic revision remains behind repository head.
- Existing clean-from-zero Alembic bootstrap limitation remains unresolved.
- Blast radius remains metadata-driven.
- In-process workflow queue remains non-durable.
- Approval request creation remains separate from runtime risk assessment.
- Existing Starlette/AnyIO TestClient deprecation warning remains.

## Next Sprint

S18 — ChangeSet & Rollback.

S18 should establish the production mutation boundary after S17 simulation, including immutable ChangeSets, auditable mutation intent, deterministic rollback/recovery semantics, and integration with the existing S16 Risk & Approval boundary.

## Handoff Notes

S17 is complete at code, test, architecture, and documentation level.

The key invariant for S18 is:

**Simulation verifies proposed behavior; ChangeSet is the only production mutation boundary.**

Any future production mutation path should preserve explicit approval, auditability, rollback capability, and clear separation between simulation and mutation.