# Adding a Capability

## 1. Define the domain contract

Capabilities are defined through `CapabilitySpec`.

A specification declares the capability identity and contract, including:

- `id`;
- `version`;
- description;
- input keys;
- output keys;
- required input keys;
- required capability dependencies;
- parameter keys;
- parameter keywords;
- input mappings;
- input types;
- output types;
- intents and intent keywords.

The specification validates its own contract during construction.

## 2. Implement the capability

A capability implements the domain `Capability` protocol.

The execution method receives a `CapabilityContext` containing execution ID, inputs, configuration and metadata.

Return a `CapabilityResult` with declared outputs and explicit success/error state.

## 3. Register it

`CapabilityRegistry` owns registered capability instances and their specifications.

Registration rejects duplicate capability IDs.

## 4. Respect execution validation

Before execution, `PlanValidator` checks exact capability version, parameters, input mappings, required inputs, mapping sources, input types, and output collisions/replacements.

During execution, `CapabilityExecutor` performs step-level validation and output checks.

Do not bypass these contracts by introducing direct execution paths.

## 5. Keep the layer boundary

The domain capability contract is framework independent.

Do not put database, HTTP, LLM, arbitrary code execution or orchestration concerns into the domain capability specification.

Deterministic execution belongs to the execution layer.

## 6. Test the contract

Cover successful execution, missing required input, invalid parameter, invalid input mapping, incompatible input type, undeclared output, output collision, and version mismatch.

Use the existing repository test patterns before introducing new abstractions.
