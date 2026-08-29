# AI Studio E-commerce Platform

An AI Studio for ecommerce data workflows. Workspaces, projects, datasets, versioned workflows, workflow executions, capability traces, and reports are platform concerns. Data quality (cleaning, normalization, extraction, validation, and QA) is the first capability family delivered by the Studio, rather than the identity of the platform itself.

## Current architecture

`FastAPI route -> Container -> StudioService / WorkflowEngine -> CapabilityExecutionService -> capability family -> repositories and reports`

## Project structure

The project is organised by responsibility. Application entry points are in `app/`; framework-independent value objects are in `domain/`; SQLAlchemy persistence models are in `database/`; and transport contracts are in `schemas/`. Existing `main.py`, `dashboard.py`, `models.domain`, `models.database`, and `api.schemas` modules remain as compatibility imports for current users and integrations.

```text
app/            API and Streamlit entry points
agents/         Workflow collaborators and LLM adapter
api/            FastAPI HTTP adapter
configs/        Runtime settings
database/       SQLAlchemy persistence models
domain/         Framework-independent value objects
repositories/   Persistence and rule repositories
reports/        Report rendering
schemas/        HTTP request/response contracts
services/       Application services and dependency container
validators/     Dynamically discovered category validators
plugins/        Reserved package for future plugin implementations
rule_engine/    Typed YAML rule parsing, loading, and validation
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

The backend is dependency-injected through the application composition root. `POST /upload`, `/validate`, `/clean`, `/extract`, and `/mapping` accept safe CSV/XLS/XLSX uploads. `GET /history` and `GET /report/{execution_id}/{format}` expose execution records and generated reports. `/validations`, `/executions`, and `/executions/{id}/reports/{format}` remain compatible routes. Mapping returns non-mutating column suggestions; there is no frontend in this sprint.

## Streamlit dashboard

Run FastAPI first, then run `streamlit run dashboard.py`. The dashboard uses `API_BASE_URL` (default `http://127.0.0.1:8000`) and communicates only through HTTP. It supports uploads and validation, health-score display, report downloads, execution history, and a health-score trend chart.

## Persistence and migrations

SQLAlchemy persists users, executions (including health scores), report paths, and validation logs. Executions may have a nullable user owner so existing integrations remain compatible. Repositories provide the application boundary for each persisted aggregate. For deployment, install dependencies and run `alembic upgrade head`; the legacy schema auto-create path remains for local/test compatibility.

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
