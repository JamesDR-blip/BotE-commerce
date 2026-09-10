# AI Studio E-commerce Platform

An AI Studio for ecommerce data workflows. Workspaces, projects, datasets, versioned workflows, workflow executions, capability traces, and reports are platform concerns. Data quality (cleaning, normalization, extraction, validation, and QA) is the first capability family delivered by the Studio, rather than the identity of the platform itself.

## Current architecture

`FastAPI Route / Streamlit -> Application Services (Workspace, Datasets, Quality, Workflows) / WorkflowEngine -> Execution Engine -> CapabilityExecutionService -> Capability Family -> Repositories / Infrastructure`

The HTTP layer is an adapter only: Studio resource operations go through `WorkspaceProjectService` and `DatasetService`, quality execution goes through `QualityService`, while workflow run and execution-history use cases go through `WorkflowRuntimeService` and `WorkflowHistoryService`. Repositories remain behind application services; capability execution remains behind the workflow engine.

## Project structure

The project is organized by responsibility following **Clean Architecture and Domain-Driven Design (DDD)**. Domain logic resides in `domain/`; application use cases in `application/`; execution coordination in `execution/`; external adapters and technical implementations in `infrastructure/`; HTTP routers in `api/`; and presentation/entry points in `app/`. Existing `main.py`, `dashboard.py`, `models.domain`, `models.database`, and `api.schemas` modules remain as compatibility entry points and imports.

```text
domain/         Core business domain entities, contracts, and services (framework-independent)
  ├── studio/       Workspace, Project, Dataset, Workflow entities, runtime models, and profiling
  ├── catalog/      Mapping, normalization, and product title extraction
  ├── quality/      HealthScoreService and anomaly detection
  ├── validation/   Missing values, format, and duplicate detection
  └── serialization/ Execution plan and requirement serializers
application/    Application use-case services
  ├── workspace/    Workspace and project management with ownership scoping
  ├── datasets/     Dataset management and tabular ingestion services
  ├── workflows/    Workflow authoring, runtime, and history services
  ├── quality/      Quality orchestration pipeline service
  └── cache.py      Application caching protocol
execution/      Execution engine and runtime orchestration
  ├── workflow/     WorkflowEngine state machine and step runner
  ├── capabilities/ Capability execution service and executor
  ├── context/      Execution context service
  ├── planning/     Execution plan validation
  └── tracing/      Execution trace collection
infrastructure/ Technical implementations and external adapters
  ├── cache/        In-memory TTLCache implementation
  ├── observability/ Structured JSON logging formatter
  ├── persistence/  Execution trace persistence adapter
  └── upload/       Secure TabularUploadReader (CSV/Excel)
capabilities/   Executable capability implementations (cleaning, extraction, normalization, qa, validation)
agents/         Workflow collaborators and optional LLM assistant (intent, requirement, planner, rules, extraction, qa, reporter, llm)
api/            FastAPI HTTP adapter and presentation routes (data, datasets, executions, studio, system, workflows)
app/            Application entry points (FastAPI, Streamlit dashboard, API client)
database/       SQLAlchemy persistence models and Alembic database migrations
repositories/   Persistence repositories for all aggregate roots
rule_engine/    Typed declarative YAML rule parser, evaluator, and validator
plugins/        Validator plugin registry and category plugins
extractors/     Deterministic product attribute extraction
reports/        Report rendering (Excel, CSV, JSON, PDF)
schemas/        HTTP request and response Pydantic contracts
configs/        Runtime configuration and environment settings
validators/     Dynamically discovered category validators
```

## Validator plugins

`plugins.registry.ValidatorRegistry` dynamically discovers validator classes from `plugins/` first and then from the legacy `validators/` package. The first validator registered for a category is used, so a plugin can be migrated without changing the validation workflow. `plugins/fashion/validator.py` is the reference migration; `validators.fashion` remains a compatibility import.

New validator plugins should subclass `plugins.base.ValidatorPlugin`, declare a unique `category`, and implement the same `validate`/optional `autofix` contract as `validators.base.CategoryValidator`. Plugin discovery imports installed project modules, so only trusted, reviewed plugin code should be deployed.

## YAML rule engine

`rule_engine` safely loads YAML through `yaml.safe_load`, parses supported declarative definitions, and evaluates them without generated Python code. `Fashion` is the reference migration. Its `validation_rules` support `required_column`, `positive_number`, `enum`, `non_empty`, and `regex` definitions. Existing descriptive `rules` lists and legacy validators remain supported during migration.

## Data-quality capability family

The initial capability family lives in `services/`, `capabilities/`, `validators/`, and `rule_engine/`: `ValidationService` preserves the existing partitioned validator execution; `HealthScoreService` preserves the clean-row score formula; `MissingValueValidation`, `FormatValidation`, and `DuplicateDetection` provide deterministic primitives; and `BusinessRuleValidation` dispatches typed YAML rules. Existing agents, validators, Rule Engine API, reports, and HTTP responses delegate to these services without changing their output contracts.

`TabularUploadReader` is the single boundary for tabular user uploads. It accepts CSV, XLS, and XLSX files, limits payload size through `MAX_UPLOAD_BYTES`, rejects path-like filenames, and escapes spreadsheet-formula cells before downstream export.

## LangGraph orchestration

`WorkflowBuilder` composes the existing deterministic agents into a LangGraph state machine. `PlannerAgent` declares the validation sequence, and `WorkflowState` is the typed hand-off contract between nodes. The graph only orchestrates classification, rule retrieval, autofix, validation, and QA; validators, rule evaluation, reports, and API contracts are unchanged.

## AI agents and inference safety

The workflow has dedicated Requirement, Category, Rule Retriever, QA, and Reporter agents. They are deterministic collaborators around the existing application services. `LLMAssistantAgent` is optional and is restricted to plain-text inference for explanations, suggested manual fixes, and report summaries. It has no tools, no code-execution path, and no generated content is evaluated by the application.

## Product extraction

`ExtractionAgent` uses the `ProductExtractor` interface and the built-in deterministic implementation to extract Brand, Model, Color, Size, Weight, Material, Voltage, Capacity, SKU, UPC, and GTIN from `product_title`, `title`, or `name`. Extraction results are read-only LangGraph state for now; they do not alter validation inputs or report/API contracts.

## FastAPI backend

The backend is dependency-injected through the application composition root. 
- Studio APIs: `POST /workspaces`, `POST /projects`, `POST /datasets`, `POST /workflows`, `POST /workflows/{id}/execute`, `GET /workflow-executions/{execution_id}`.
- Data Quality APIs: `POST /upload`, `/validate`, `/clean`, `/extract`, and `/mapping` accept safe CSV/XLS/XLSX uploads.
- History & Reports: `GET /history`, `GET /executions`, and `GET /report/{execution_id}/{format}` expose execution records and generated reports.
- `/validations`, `/executions`, and `/executions/{id}/reports/{format}` remain compatible routes.

## Streamlit dashboard

Run FastAPI first, then run `streamlit run dashboard.py`. The dashboard uses `API_BASE_URL` (default `http://127.0.0.1:8000`) and communicates only through HTTP. It supports uploads and validation, health-score display, report downloads, execution history, and a health-score trend chart.

## Persistence and migrations

SQLAlchemy persists users, workspaces, projects, datasets, workflows, workflow versions, workflow executions, execution traces, report paths, and validation logs. Executions may have a nullable user owner so existing integrations remain compatible. Repositories provide the application boundary for each persisted aggregate. For deployment, install dependencies and run `alembic upgrade head` (current migration head: `b05fd7d45c87`); the legacy schema auto-create path remains for local/test compatibility.

## Run

```bash
pip install -r requirements.txt
uvicorn api.main:create_app --factory --reload
pytest tests
```

For compatibility, `python main.py` and `streamlit run dashboard.py` remain valid entry points.

## Configuration and logging

Runtime configuration is loaded by Pydantic Settings from environment variables and, for local development, an optional `.env` file. Copy `.env.example` to `.env` and set values appropriate to the environment. Do not commit `.env` or production credentials.

Important variables include `ENVIRONMENT` (`development`, `test`, or `production`), `DATABASE_URL`, `REPORTS_PATH`, `MAX_UPLOAD_BYTES`, `LOG_LEVEL`, and the optional `GOOGLE_API_KEY`. `LOG_LEVEL` accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

Application logs are emitted as JSON to standard error. Each event includes a timestamp, level, logger name, message, and event-specific fields such as an execution ID when available.

Submit a CSV or Excel file to `POST /validations`, optionally with a `category` form field. Existing endpoints remain available: `/health`, `/categories`, `/executions`, and report downloads.
