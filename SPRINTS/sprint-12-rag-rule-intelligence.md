# SPRINT 12: RAG & Semantic Rule Intelligence

## Status
Ready / In Progress (Current Sprint)

## Objective
Enable semantic search and intelligent retrieval of category validation rules and business policies using vector embeddings, moving beyond static category lookups to context-aware rule selection.

## Architectural Layer Impact
- **Domain Layer (`domain/`):**
  - Define `RuleRetriever` domain interface.
  - Define `RuleQuery`, `RetrievedRuleMatch`, `SemanticRulePack` value objects.
- **Infrastructure Layer (`infrastructure/`):**
  - Implement vector store adapter using Chroma / FAISS.
  - Implement rule embedding pipeline (generating vector representations for YAML declarative rules).
- **Application Layer (`application/`):**
  - Implement `RuleIntelligenceService` to coordinate semantic querying and filtering.
- **Agents Layer (`agents/`):**
  - Connect `RuleRetrieverAgent` to `RuleRetriever` port to fetch rules dynamically based on tabular schema and column semantics.
- **API Layer (`api/routes/rules.py`):**
  - `POST /rules/search`: Semantic query over rules library.
  - `POST /rules/recommend`: Suggest validation rules based on dataset profile.

## Security & Constraints
- Vector store operations must be isolated in `infrastructure/`.
- Domain layer must have zero dependencies on Chroma, FAISS, or embedding libraries.
- No dynamic code execution from retrieved rules; all rules must map to registered declarative primitives.

## Verification Criteria
- Unit tests for `RuleRetriever` interface and vector adapter.
- Semantic similarity matching test verifying that ambiguous column names match the correct domain rules.
- 100% green tests in `pytest tests`.
