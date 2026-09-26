# Validation Architecture

## Plan validation

`PlanValidator` validates an `ExecutionPlan` against the registered capability contracts before capability execution.

Validation includes:

1. capability version matching;
2. parameter validation;
3. input mapping validation;
4. required input availability;
5. mapping source availability;
6. input type compatibility;
7. output collision and replacement rules;
8. registration of outputs for subsequent steps.

A plan therefore cannot rely on an undeclared parameter, unknown mapping source, missing required input, incompatible typed input, or an undeclared output replacement.

## Execution boundary

The capability execution service validates the plan and registry before executing the plan. The executor then performs step-level validation and records execution trace information.

The execution layer owns workflow runtime behavior; capability contracts remain framework-independent domain contracts.

## Shadow simulation

The ShadowExecutionRunner provides an ephemeral simulation path.

For in-memory simulation it:

- isolates inputs;
- executes the capability plan;
- isolates outputs;
- builds a diff;
- returns SimulationResult.

For streaming simulation it processes persisted dataset chunks and accumulates bounded diff information.

Simulation can report changed keys, changed rows, added rows, removed rows, before/after columns, bounded row-level diffs, and whether the diff was truncated.

Simulation is not production execution persistence.
