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
```

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
