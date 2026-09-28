# S28 Production Security Sign-off Report

**Status: NOT APPROVED FOR PRODUCTION GA**  
**Review date:** 2026-09-28  
**Review scope:** repository hardening changes and automated evidence available in this workspace.

## Evidence Reviewed

- Full test suite: 977 passed, 3 warnings in 104.72 seconds.
- Focused hardening suite: 74 passed, 2 warnings.
- Bandit report: 0 findings.
- pip-audit raw report: five ChromaDB advisory records (four unique advisory IDs; one duplicate record).
- Blocking pip-audit with documented exclusions: no known applicable findings.
- Local Alembic upgrade: `20260926_01` → `20260928_01`; one head.
- Chroma configuration uses `chromadb.PersistentClient`; the repository test asserts no remote Chroma client/server configuration.

## Implemented Controls

- Nginx request-rate limiting for the API proxy path.
- Connector URL validation for HTTPS origin-only URLs and local/private/reserved targets.
- ChangeSet metadata and item snapshot integrity commitments, plus artifact checks before Apply/Rollback.
- Audit event and workspace hash-chain verification on audit reads.
- Fuzz coverage for malformed approval payloads.
- CI static security and dependency scanning.

## Findings and Limitations

1. The four unique ChromaDB advisory IDs remain visible in the raw report. They are excluded from the blocking scan only because the current configuration uses local embedded storage and does not enable the separately hosted Chroma server API. Reassess before any server exposure or when upstream fixes become available.
2. No independent penetration test was performed as part of this repository verification.
3. The SOC 2 / GDPR checklist requires review by security, privacy, legal, and operational stakeholders. No compliance certification or legal determination is claimed.
4. Docker runtime verification, production telemetry collector integration, alerting, and an operational restore exercise remain pending deployment validation.
5. Three non-failing test warnings remain: Hypothesis cache configuration, Starlette/AnyIO TestClient deprecation, and duplicate `rules/fashion.yaml` fixture.

## Decision

Core S28 repository implementation is verified against the recorded automated checks. Production GA sign-off remains **pending** until the independent penetration test is completed, findings are resolved, compliance stakeholders review the checklist, and deployment/operations validation is completed.
