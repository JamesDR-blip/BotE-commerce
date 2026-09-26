# Autonomous Execution Loop

## Scope

The platform product loop is:

```text
Detect -> Diagnose -> Plan -> Simulate -> Risk -> Approve -> Apply -> Verify -> Sync -> Audit -> Learn
```

This document describes the execution-related boundaries demonstrated by the current implementation.

## Plan

An execution plan contains ordered capability steps. Each step identifies a capability and an exact capability version.

PlanValidator verifies the plan against the registered capability contracts before execution.

## Simulate

ShadowExecutionRunner executes a plan against isolated inputs and produces a SimulationResult with a bounded diff.

The simulation path supports both in-memory and streaming execution modes.

## Execute

CapabilityExecutionService coordinates plan validation, capability execution and execution tracing.

CapabilityExecutor resolves the registered capability, checks the exact capability version, validates input mappings and parameters, maps inputs, validates input types, executes the capability, validates outputs, prevents undeclared or colliding outputs, and records trace state.

The execution service also integrates telemetry and optional lineage context.

## Governance boundary

Agents reason and propose; deterministic execution is performed by the execution layer.

Production mutation is governed through the platform's ChangeSet boundary and associated risk/approval mechanisms.

## Shadow versus production

```text
Production: plan -> validate -> execute -> trace/lineage/telemetry

Simulation: plan -> isolate -> execute -> diff -> SimulationResult
```

Simulation should be used when the caller needs to inspect expected changes without treating the result as production execution.
