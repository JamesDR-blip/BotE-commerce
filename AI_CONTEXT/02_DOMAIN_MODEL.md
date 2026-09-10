# DOMAIN MODEL

This document defines the domain models, aggregates, value objects, and planned entities for the platform.

---

## 1. Implemented Domain Aggregates & Entities

### Studio Core (`domain/studio/`)
- **`Workspace`** (`domain/studio/workspace.py`): Root boundary for multi-tenant data operations. Owns projects, scoped to an owner (`user_id`).
- **`Project`** (`domain/studio/project.py`): Logical container for datasets and workflows belonging to a Workspace.
- **`Dataset`** (`domain/studio/dataset.py`): Tabular data asset metadata (name, file path, size, row/column counts, project association).
- **`Workflow`** (`domain/studio/workflow.py`): Authoring entity defining an automated data pipeline.
- **`WorkflowVersion`** (`domain/studio/workflow.py`): Immutable snapshot of a workflow definition with its execution plan.
- **`WorkflowExecution`** (`domain/studio/runtime.py`): Instance of a workflow run, tracked by `WorkflowExecutionStatus`.

### Execution & Capability Domain Contracts (`domain/`)
- **`ExecutionPlan`** & **`PlanStep`** (`domain/execution_plan.py`): Dependency-ordered sequence of capabilities to execute.
- **`ExecutionTrace`** & **`CapabilityExecutionRecord`** (`domain/execution_trace.py`): Fine-grained tracing of capability execution status, inputs, outputs, and durations.
- **`ExecutionContext`** (`domain/execution_context.py`): Runtime parameter passing and state context between capability steps.
- **`ValidationRequirement`** & **`WorkflowRequirement`** (`domain/requirement.py`): User intent represented as structured execution requirements.
- **`CapabilitySpec`**, **`CapabilityContext`**, **`CapabilityResult`** (`domain/capabilities.py`): Standard contract for pluggable capabilities.
- **`CapabilityDependency`** (`domain/capability_dependency.py`): Explicit capability dependency graph definition.

---

## 2. Implemented Domain Services & Value Objects

### Catalog & Normalization (`domain/catalog/`)
- **`MappingService`**: Suggests and maps column aliases to canonical schema fields.
- **`NormalizationService`**: Standardizes whitespace, case, price formatting, and status flags.
- **`ProductAttributes`**: Typed domain value object holding extracted product attributes (Brand, Model, Color, Size, Material, Weight, Voltage, Capacity, SKU, UPC, GTIN).

### Data Quality & QA (`domain/quality/`)
- **`HealthScoreService`**: Deterministic scoring formula: `(valid_rows / total_rows) * 100` with severities and deduction rules.
- **`detect_anomalies`**: Statistical and rule-based anomaly detection on tabular distributions.

### Validation Primitives (`domain/validation/`)
- **`MissingValueValidation`**: Identifies mandatory empty fields and generates issues.
- **`FormatValidation`**: Validates email, phone, regex patterns, numeric ranges, and date formats.
- **`DuplicateDetection`**: Identifies exact and normalized duplicate records across primary key or canonical title fields.

### Serialization (`domain/serialization/`)
- **`execution_plan.py`**: Round-trip serialization/deserialization for execution plans.
- **`requirement.py`**: Round-trip serialization/deserialization for workflow requirements.

---

## 3. Database Persistence Records (`database/models.py`)

| Domain Aggregate | Database Table | SQLAlchemy Model |
|---|---|---|
| Workspace | `workspaces` | `WorkspaceRecord` |
| Project | `projects` | `ProjectRecord` |
| Dataset | `datasets` | `DatasetRecord` |
| Workflow | `workflows` | `WorkflowRecord` |
| WorkflowVersion | `workflow_versions` | `WorkflowVersionRecord` |
| WorkflowExecution | `workflow_executions` | `WorkflowExecutionRecord` |
| ExecutionTrace | `execution_traces` | `ExecutionTraceRecord` |
| CapabilityTrace | `capability_execution_traces` | `CapabilityExecutionTraceRecord` |
| Validation Run | `executions` | `ExecutionRecord` |
| Validation Log | `validation_logs` | `ValidationLogRecord` |
| Report | `reports` | `ReportRecord` |
| User / Tenant | `users` | `UserRecord` |

---

## 4. Planned Roadmap Entities

The following entities are defined in the product vision and will be introduced in subsequent sprints:

- **Product & ProductVersion**: Canonical multi-channel product catalog model.
- **ChangeSet & ChangeSetItem**: Immutable mutation boundary capturing exact diffs before applying changes to production data.
- **RiskPolicy & RiskScore**: Policy-driven assessment of proposed operations based on impact radius.
- **ConfidenceScore**: Statistical assessment of automated fixes and extractions.
- **Approval & Rollback**: Human-in-the-loop approval workflows and reversible change mechanisms.
- **DataLineageEvent & AuditEvent**: End-to-end data provenance tracking.
- **Connector, SyncJob & SyncAttempt**: External channel synchronization (Shopify, Amazon, TikTok Shop, Shopee, Lazada).
- **RulePack**: Versioned packages of domain business rules.
- **Memory**: Persistent agent memory across sessions.

