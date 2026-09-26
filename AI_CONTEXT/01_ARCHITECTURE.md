# ARCHITECTURE

## Runtime & Tech Stack

- **Language:** Python 3.13
- **Web API:** FastAPI
- **Dashboard:** Streamlit
- **Persistence:** SQLAlchemy 2.0 + Alembic (Current Head: `b05fd7d45c87`)
- **Orchestration:** LangGraph / Custom State Machine (`WorkflowEngine`)
- **Validation & Settings:** Pydantic v2
- **Rule Engine:** Safe YAML (`yaml.safe_load`) Declarative Rule Engine

## Architecture: Clean Architecture + DDD

The platform is structured into five distinct architectural layers following Clean Architecture and Domain-Driven Design principles:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Presentation / Interfaces                 │
│  - api/ (FastAPI routers: data, datasets, studio, workflows) │
│  - app/ (main.py, dashboard.py, api_client.py)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Application Layer                      │
│  - application/workspace/ (WorkspaceProjectService)         │
│  - application/datasets/  (DatasetService, DatasetIngestion) │
│  - application/workflows/ (Authoring, Runtime, History)      │
│  - application/quality/   (QualityService orchestration)     │
│  - application/cache.py   (Cache protocol)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Execution Layer                        │
│  - execution/workflow/    (WorkflowEngine state machine)     │
│  - execution/capabilities/(CapabilityExecutionService)       │
│  - execution/context/     (ExecutionContextService)          │
│  - execution/planning/    (PlanValidator)                    │
│  - execution/tracing/     (ExecutionTraceCollector)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         Domain Layer                         │
│  - domain/studio/       (Workspace, Project, Dataset, ...)   │
│  - domain/catalog/      (Mapping, Normalization, Extraction) │
│  - domain/quality/      (HealthScoreService, Anomalies)      │
│  - domain/validation/   (Missing values, Format, Duplicates) │
│  - domain/serialization/(ExecutionPlan, Requirement)         │
│  - domain contracts     (Capability, Registry, Resolver)     │
└──────────────────────────────┬──────────────────────────────┘
                               ▲
                               │ (Inversion of Control)
┌──────────────────────────────┴──────────────────────────────┐
│                     Infrastructure Layer                     │
│  - infrastructure/cache/        (In-memory TTLCache)         │
│  - infrastructure/upload/       (TabularUploadReader)        │
│  - infrastructure/observability/(Structured JSON logging)    │
│  - infrastructure/persistence/  (ExecutionTracePersistence)  │
│  - database/                    (SQLAlchemy models & Alembic)│
│  - repositories/                (Repository implementations) │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities & Directory Mapping

### 1. Domain Layer (`domain/`)
- Pure business logic, entity models, value objects, and domain contracts.
- **`domain/studio/`**: `Workspace`, `Project`, `Dataset`, `Workflow`, `WorkflowVersion`, `WorkflowExecution`, `DatasetProfileService`.
- **`domain/catalog/`**: `MappingService`, `NormalizationService`, `ProductAttributes`, `title_extraction`.
- **`domain/quality/`**: `HealthScoreService`, `detect_anomalies`.
- **`domain/validation/`**: `MissingValueValidation`, `FormatValidation`, `DuplicateDetection`.
- **`domain/serialization/`**: Serializers/deserializers for `ExecutionPlan` and `WorkflowRequirement`.
- **Root `domain/` contracts**: `CapabilityRegistry`, `CapabilitySelector`, `DependencyResolver`, `IntentResolver`, `ExecutionPlan`, `ExecutionTrace`, `ExecutionContext`, `type_contracts.py`, `exceptions.py`.

### 2. Application Layer (`application/`)
- Business use-case coordinators and transaction scripts.
- **`application/workspace/`**: `WorkspaceProjectService` (tenant/owner-scoped workspace & project CRUD).
- **`application/datasets/`**: `DatasetService` (dataset registration), `DatasetIngestionService` (tabular file parsing & profiling).
- **`application/workflows/`**: `WorkflowAuthoringService` (definitions & versioning), `WorkflowRuntimeService` (execution triggers), `WorkflowHistoryService` (execution queries).
- **`application/quality/`**: `QualityService` (runs end-to-end data quality pipeline, report generation, cache check, persistence).
- **`application/cache.py`**: Protocol defining cache contracts (`get`, `set`).

### 3. Execution Layer (`execution/`)
- Workflow state machine, capability dispatching, and trace management.
- **`execution/workflow/`**: `WorkflowEngine` (loads execution plans, transitions state: `CREATED` -> `RUNNING` -> `COMPLETED`/`FAILED`, failure recovery, snapshotting).
- **`execution/capabilities/`**: `CapabilityExecutionService` (dependency resolution and chain execution), `CapabilityExecutor` (execution context handling and trace recording).
- **`execution/context/`**: `ExecutionContextService`.
- **`execution/planning/`**: `PlanValidator` (validates execution plan steps against registered capability specs and types).
- **`execution/tracing/`**: `ExecutionTraceCollector` (fine-grained trace collection).

### 4. Infrastructure Layer (`infrastructure/`, `database/`, `repositories/`)
- Technical implementations, external integrations, and persistence.
- **`infrastructure/upload/`**: `TabularUploadReader` (secure CSV, XLS, XLSX parsing, formula injection sanitization, size checks, path traversal prevention).
- **`infrastructure/cache/`**: `TTLCache` (in-memory TTL cache implementing `application.cache.Cache`).
- **`infrastructure/observability/`**: Structured JSON logging (`StructuredJsonFormatter`).
- **`infrastructure/persistence/`**: `ExecutionTracePersistence`.
- **`database/`**: SQLAlchemy models (`models.py`) and Alembic migrations (`migrations/versions/`).
- **`repositories/`**: Concrete repository implementations (`workspaces`, `projects`, `datasets`, `workflows`, `workflow_executions`, `execution_traces`, `capability_execution_traces`, `executions`, `rules`, `users`).

### 5. Presentation / Interface Layer (`api/`, `app/`)
- **`api/routes/`**: FastAPI HTTP endpoints:
  - `system.py`: `/health`, `/categories`
  - `studio.py`: `/workspaces`, `/projects`
  - `datasets.py`: `/datasets`, `/projects/{project_id}/datasets/upload`
  - `workflows.py`: `/workflows`, `/workflows/{workflow_id}/execute`, `/workflow-executions/{execution_id}`
  - `data.py`: `/upload`, `/clean`, `/extract`, `/mapping`, `/validate`, `/validations`
  - `executions.py`: `/executions`, `/history`, `/report/{execution_id}/{format}`
- **`app/`**: Application entry points:
  - `main.py`: FastAPI server startup
  - `dashboard.py`: Streamlit Dashboard
  - `api_client.py`: Typed HTTP client consumed by Streamlit

## Composition Root

- **`services/container.py`**: Instantiates settings, repositories, services, agents, and capabilities without global mutable state.

## Core Capabilities (`capabilities/`)

- `CleaningCapability`: Cleans missing/invalid values and applies auto-fixes.
- `NormalizationCapability`: Normalizes columns and standardizes product attributes.
- `ExtractionCapability`: Extracts brand, model, color, size, etc., from product titles.
- `ValidationCapability`: Validates business rules against dynamic category rules.
- `QACapability`: Computes health score and flags anomalies.

## Agents (`agents/`)

- `IntentClassifier`: Classifies user text intents to execution requirements.
- `RequirementAgent`: Builds execution requirements from user intent.
- `PlannerAgent`: Assembles dependency-ordered execution plans.
- `RuleRetrieverAgent`: Loads category rules from safe YAML repository.
- `ExtractionAgent`: Extracts product attributes via deterministic or model extractors.
- `CategoryAgent`: Classifies dataset domain (Fashion, Cosmetics, Home Appliances).
- `ParameterResolver`: Dynamically maps parameters between capability steps.
- `RequirementInterpreter`: Interprets natural language requirements into capability parameters.
- `QAAgent`: Assesses dataset health score and flags anomalies.
- `ReporterAgent`: Generates structured reports in CSV, JSON, Excel, PDF.
- `LLMAssistantAgent`: Optional text-only explanation assistant (no code execution).

## Persistence

- **Development:** SQLite (`data_quality.db`)
- **Production:** PostgreSQL
- **Alembic Migration Head:** `20260923_01` (`20260923_01_add_compliance_policies.py`)
- **Vector Store:** Chroma (planned for Sprint S12+ RAG / Rule Intelligence)

## Dependency Rules

```text
Domain  <--  Application  <--  Execution / Presentation
   ▲
   └──  Infrastructure (Dependency Inversion via Interfaces)
```

- **Domain** must NOT depend on:
  - FastAPI / Starlette
  - Streamlit
  - SQLAlchemy / Alembic
  - LangGraph
  - External LLM providers
