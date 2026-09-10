\# ARCHITECTURE



\## Runtime



Python 3.13

FastAPI

Streamlit

SQLAlchemy 2

Alembic

LangGraph

Pydantic v2



\## Architecture



Clean Architecture + DDD



Domain

Application

Execution

Infrastructure

Interface



\## Composition Root



services/container.py



\## Core Components



Capabilities:

\- CleaningCapability

\- NormalizationCapability

\- ExtractionCapability

\- ValidationCapability

\- QACapability



Agents:

\- IntentClassifier

\- RequirementAgent

\- PlannerAgent

\- RuleRetrieverAgent

\- QAAgent

\- ReporterAgent

\- ProductAttributeExtractionAgent



\## Persistence



Development:

SQLite



Production:

PostgreSQL



Vector Store:

Chroma planned / infrastructure only



\## Dependency Rules



Domain

&#x20; ↓

Application

&#x20; ↓

Execution / Infrastructure



Domain must not depend on:

\- FastAPI

\- Streamlit

\- SQLAlchemy

\- LangGraph

\- Chroma

\- LLM providers

