# AI Data Quality Platform

An incremental foundation for an AI Data Studio that cleans, validates, enriches, and reports on ecommerce data. The current production path is a FastAPI validation workflow backed by dynamically discovered category validators, YAML rules, reports, and execution history.

## Current architecture

`FastAPI route -> Container -> TabularUploadReader -> QualityService -> workflow agents -> validators/rules -> reports/repository`

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

## Validation services

Reusable validation mechanics live in `services/`: `ValidationService` preserves the existing partitioned validator execution; `HealthScoreService` preserves the clean-row score formula; `MissingValueValidation`, `FormatValidation`, and `DuplicateDetection` provide deterministic primitives; and `BusinessRuleValidation` dispatches typed YAML rules. Existing agents, validators, Rule Engine API, reports, and HTTP responses delegate to these services without changing their output contracts.

`TabularUploadReader` is the single boundary for tabular user uploads. It accepts CSV, XLS, and XLSX files, limits payload size through `MAX_UPLOAD_BYTES`, rejects path-like filenames, and escapes spreadsheet-formula cells before downstream export.

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
