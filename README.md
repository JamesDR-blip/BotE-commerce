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

Submit a CSV or Excel file to `POST /validations`, optionally with a `category` form field. Existing endpoints remain available: `/health`, `/categories`, `/executions`, and report downloads.
