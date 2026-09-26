# ROADMAP

## Completed Sprints

- **S00 Architecture Audit & Baseline Refactor**: Composition root, application factory, initial audit.
- **S01 Project Structure & Baseline Standards**: Layering foundation, pytest test harnesses.
- **S02 Configuration & Structured Logging**: Pydantic settings, JSON structured logging.
- **S03 Plugin Architecture**: Dynamic ValidatorRegistry, validator discovery, category plugins.
- **S04 Safe YAML Rule Engine**: yaml.safe_load, declarative rule evaluator (required, regex, enum, range).
- **S05 Capability Decomposition**: Independent capabilities (Cleaning, Normalization, Extraction, Validation, QA).
- **S06 LangGraph Orchestration**: Typed state transitions, dependency ordering.
- **S07 AI Collaborator Agents**: Intent classification, requirement planning, QA, reporting, optional LLM assistant.
- **S08 Product Attribute Extraction**: Deterministic extraction of brand, model, size, color, SKU, GTIN, UPC.
- **S09 FastAPI Presentation Layer**: REST endpoints (/upload, /validate, /clean, /extract, /mapping, /history, /report).
- **S10 Persistence & Alembic Migrations**: PostgreSQL & SQLite support.
- **S11 Streamlit Dashboard & Client**: Decoupled HTTP client, interactive validation & report download.
- **Clean Architecture & DDD Refactoring**: Reorganized into domain/, application/, execution/, infrastructure/ packages; introduced Cache protocol and domain serialization.
- **S12 RAG / Rule Intelligence**: RuleRetriever abstraction, semantic rule search, dynamic category rule packs.
- **S13 Agent Memory & Execution Context**: Tenant-scoped persistent agent memory, correction events, execution learning, PII redaction, expiration, and memory-aware requirement parameter resolution.
- **S14 Performance**: Streaming tabular ingestion, chunked processing, async execution workers.
- **S15 Data Health Command Center**: Live health scores, issue tracking, and automated fix recommendations.
- **S16 Risk & Approval Engine**: RiskPolicy domain model, confidence scoring, and human-in-the-loop approval gates.
- **S17 Shadow Mode & Simulation**: Safe dry-run workflow simulation, bounded diff verification, read-only streaming, and zero production mutation.
- **S18 ChangeSet & Rollback**: Immutable ChangeSets, atomic production mutation, candidate artifact materialization, HITL approval integration, optimistic-concurrency guarded rollback, and owner-scoped ChangeSet APIs.
- **S19 Data Lineage & Audit Trail**: Capability-level lineage, SHA-256 hash-chained audit events, owner/workspace-scoped APIs, and transactional mutation auditing.
- **S20 Autonomous Agent Operations**: Governed closed-loop operations with deterministic guardrails, risk evaluation, ChangeSet preparation, approval/apply, verification, and learning.
- **S21 Channel Sync & Multi-Platform Connectors**: Canonical product/channel sync framework, deterministic projection, idempotent synchronization, encrypted credentials, Shopify/Amazon connectors, and governed sync APIs.
- **S22 AI Copilot for Data Operations**: Conversational dataset/health queries, governed workflow authoring, simulation/execution tool dispatch, SSE streaming, Streamlit Copilot UI, and safe approval metadata presentation.
- **S23 Marketplace & Extensibility Ecosystem**: Signed declarative RulePack packaging, secure archive inspection, Ed25519 verification, filesystem-backed package/version lifecycle, authenticated marketplace APIs, and safe RuleEngine integration.
- **S24 Enterprise Governance**: Role-based access control (RBAC), multi-tenancy quotas, deterministic compliance policy enforcement, tenant isolation, and governance verification.
- **S25 Observability**: OpenTelemetry tracing, Prometheus metrics, and execution dashboard.
- **S26 DevOps**: Production multi-stage Docker image, Docker Compose deployment topology, Nginx reverse proxy, Redis-backed worker deployment, CI/CD automation, semantic-version release workflow, image vulnerability scanning, production environment template, and deployment documentation.
**S27 Documentation**: Interactive API specs, architecture diagrams, and developer/operator guides

## Current Sprint

- **S27 Documentation — COMPLETE**.

## Future Roadmap
- **S28 Hardening**: Security audit, penetration testing, fuzzing, and compliance certification.

### S26 — DevOps & Platform Reliability

Status: COMPLETE

Focus:

- CI/CD and deployment reliability.
- Production observability integration.
- Runtime health and resilience.
- Operational alerting.
- Platform reliability and deployment verification.

Delivered in S26:
- Production multi-stage Dockerfile with non-root runtime.
- Production Docker Compose topology with Nginx, PostgreSQL, Redis, API, dashboard, and two worker replicas.
- Redis-backed production workflow execution.
- PR CI with Ruff, Black, MyPy, pytest, and 90% coverage enforcement.
- Semantic-version release automation with GHCR publication and Trivy scanning.
- Production environment template and deployment documentation.

Remaining platform concerns:
- Production telemetry collector/Prometheus/Grafana deployment wiring.
- Operational alerting.
- Docker runtime deployment verification in a Docker-enabled environment.

### S27 — Developer Documentation & API Specifications

Status: COMPLETE

Delivered:

- Added the documentation portal under docs/.
- Added API documentation aligned with the generated FastAPI OpenAPI 3.1 specification.
- Added architecture sequence diagrams/guides for Ingestion, Validation, Autonomous Loop, and Channel Sync.
- Added developer guides for Adding a Capability and Writing a Plugin.
- Added operator guides for Disaster Recovery, Rollback, and Database Migration.
- Preserved the existing production deployment documentation.
- Added router tags and operation-level OpenAPI summaries/descriptions for all 61 API operations.
- Validated OpenAPI schema references and response declarations.
- Validated Markdown links and code fences.

Verification:

- OpenAPI 3.1.0.
- 60 paths, 61 operations, 71 schemas.
- Full regression: 938 passed, 2 warnings.
- python -m compileall -q api: PASS.
- git diff --check: PASS.
- No new database migration; Alembic head remains 20260923_01.

Next sprint: S28 Hardening.
