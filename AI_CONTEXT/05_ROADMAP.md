# ROADMAP

## Completed Sprints

- **S00 Architecture Audit & Baseline Refactor**: Composition root, application factory, initial audit.
- **S01 Project Structure & Baseline Standards**: Layering foundation, pytest test harnesses.
- **S02 Configuration & Structured Logging**: Pydantic settings, JSON structured logging.
- **S03 Plugin Architecture**: Dynamic `ValidatorRegistry`, validator discovery, category plugins.
- **S04 Safe YAML Rule Engine**: `yaml.safe_load`, declarative rule evaluator (required, regex, enum, range).
- **S05 Capability Decomposition**: Independent capabilities (`Cleaning`, `Normalization`, `Extraction`, `Validation`, `QA`).
- **S06 LangGraph Orchestration**: Typed state transitions, dependency ordering.
- **S07 AI Collaborator Agents**: Intent classification, requirement planning, QA, reporting, optional LLM assistant.
- **S08 Product Attribute Extraction**: Deterministic extraction of brand, model, size, color, SKU, GTIN, UPC.
- **S09 FastAPI Presentation Layer**: REST endpoints (`/upload`, `/validate`, `/clean`, `/extract`, `/mapping`, `/history`, `/report`).
- **S10 Persistence & Alembic Migrations**: PostgreSQL & SQLite support, migrations up to `b05fd7d45c87`.
- **S11 Streamlit Dashboard & Client**: Decoupled HTTP client, interactive validation & report download.
- **Clean Architecture & DDD Refactoring**: Reorganized into `domain/`, `application/`, `execution/`, `infrastructure/` packages; introduced `Cache` protocol and domain serialization.
- **S12 RAG / Rule Intelligence**: RuleRetriever abstraction, semantic rule search, dynamic category rule packs.
- **S13 Agent Memory & Execution Context**: Tenant-scoped persistent agent memory, correction events, execution learning, PII redaction, expiration, and memory-aware requirement parameter resolution.

---

## Current Sprint

- **S14 Performance**: Streaming tabular ingestion, chunked processing, async execution workers.

---

## Future Roadmap

- **S15 Data Health Command Center**: Live health scores, issue tracking, and automated fix recommendations.
- **S16 Risk & Approval**: RiskPolicy domain model, confidence scoring, human-in-the-loop approval gates.
- **S17 Shadow Mode**: Dry-run simulation and diff verification before mutation.
- **S18 ChangeSet & Rollback**: Immutable change sets, automated rollbacks, and recovery transactions.
- **S19 Lineage & Audit**: Full data provenance, audit trails, and event sourcing.
- **S20 Autonomous Agent Operations**: Guardrailed self-healing data pipelines.
- **S21 Channel Sync**: Multi-channel connectors (Shopify, Amazon, TikTok Shop, Shopee, Lazada).
- **S22 Copilot**: Natural language conversational assistant for dataset querying and pipeline authoring.
- **S23 Marketplace**: Community rule packs, custom validator plugins, and connectors.
- **S24 Enterprise Governance**: Role-based access control (RBAC), multi-tenancy quotas, audit compliance.
- **S25 Observability**: OpenTelemetry tracing, Prometheus metrics, and execution dashboard.
- **S26 DevOps**: Production Docker Compose, Helm charts, CI/CD pipeline automation.
- **S27 Documentation**: Interactive API specs, architecture diagrams, and developer guides.
- **S28 Hardening**: Security audit, penetration testing, fuzzing, and compliance certification.
