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
- **Clean Architecture & DDD Refactoring**: Reorganized into domain/, application/, execution/, infrastructure/ packages; introduced Cache protocol and domain serialization.
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
- **S22 AI Copilot for Data Operations — COMPLETE**: Conversational dataset/health queries, governed workflow authoring, simulation/execution tool dispatch, SSE streaming, Streamlit Copilot UI, and safe approval metadata presentation.

- **S23 Marketplace & Extensibility Ecosystem — COMPLETE**: Signed declarative RulePack packaging, secure archive inspection, Ed25519 verification, filesystem-backed package/version lifecycle, authenticated marketplace APIs, and safe RuleEngine integration.
## Current Sprint

- **S23 Marketplace & Extensibility Ecosystem — COMPLETE**.

## Next Sprint

- **S24 Enterprise Governance**.

## Future Roadmap

- **S24 Enterprise Governance**: Role-based access control (RBAC), multi-tenancy quotas, audit compliance.
- **S25 Observability**: OpenTelemetry tracing, Prometheus metrics, and execution dashboard.
- **S26 DevOps**: Production Docker Compose, Helm charts, CI/CD pipeline automation.
- **S27 Documentation**: Interactive API specs, architecture diagrams, and developer guides.
- **S28 Hardening**: Security audit, penetration testing, fuzzing, and compliance certification.

## S21 — Channel Sync & Multi-Platform Connectors

**Status:** COMPLETE

Delivered:

- CanonicalProduct and ChannelMapping domain contracts.
- Channel, SyncJob, SyncAttempt and Connector contracts.
- Deterministic canonical-product projection.
- Idempotent channel synchronization.
- Channel mapping reconciliation and delta/noop handling.
- Encrypted channel credentials with fail-closed behavior.
- Bounded HTTP retry/backoff.
- Shopify connector.
- Amazon SP-API connector.
- Channel synchronization API.
- Repository, service, connector and API test coverage.

Deferred:

- TikTok Shop connector.
- Shopee connector.
- Lazada connector.
- Production-grade Amazon SP-API SigV4 authentication/signing.
- Dedicated distributed/channel-specific rate limiting.
- Durable asynchronous channel workers.
- Cross-product external compensation/reconciliation.

**Verification:** 706 tests passed in the full regression suite.
