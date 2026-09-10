# SPRINT 16: Risk & Approval Engine

## Status
Backlog

## Objective
Introduce policy-driven risk assessment and confidence scoring, enforcing human-in-the-loop approval gates before applying high-risk data mutations.

## Architectural Layer Impact
- **Domain Layer (`domain/`):**
  - Define `RiskPolicy` aggregate root.
  - Define `RiskScore` (Low, Medium, High, Critical) and `ConfidenceScore` value objects.
  - Define `ApprovalRequest`, `ApprovalDecision` (Approved, Rejected, Expired).
- **Application Layer (`application/`):**
  - Implement `RiskAssessmentService` evaluating proposed operation blast radius.
  - Implement `ApprovalService` managing approval lifecycles.
- **Database Layer (`database/` & `repositories/`):**
  - `ApprovalRecord`, `RiskAssessmentRecord` SQLAlchemy models and Alembic migration.
  - `ApprovalRepository`.
- **API Layer (`api/routes/approvals.py`):**
  - `GET /approvals/pending`, `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject`.

## Security & Constraints
- High-risk operations cannot execute without valid approval token.
- Approver must have appropriate permission role.

## Verification Criteria
- Tests verifying that High-Risk operations pause execution in `PENDING_APPROVAL` status.
- Tests verifying that execution resumes upon approval and cancels upon rejection.
