# SPRINT 17: Shadow Mode & Simulation

## Status
Backlog

## Objective
Provide a safe dry-run simulation mode that executes pipelines in an isolated sandbox, calculating exact before/after row diffs and impact analysis without mutating production datasets.

## Architectural Layer Impact
- **Execution Layer (`execution/`):**
  - Implement `ShadowExecutionRunner` in `WorkflowEngine`.
  - Enforce read-only isolation (intercept and prevent database/external mutations).
- **Domain Layer (`domain/`):**
  - Define `SimulationResult`, `DiffPreview`, `ImpactAnalysis` value objects.
- **Application Layer (`application/`):**
  - Implement `SimulationService`.
- **API Layer (`api/routes/`):**
  - `POST /workflows/{id}/simulate`: Run pipeline in shadow mode and return diff preview.

## Security & Constraints
- Zero production mutation during simulation.
- Memory-bounded diff generation for large datasets.

## Verification Criteria
- Tests confirming zero state changes occur in the database during simulation.
- Tests verifying accuracy of generated diff previews.
