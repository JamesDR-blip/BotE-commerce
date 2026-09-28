# SOC 2 / GDPR Readiness Checklist

This checklist is an internal engineering readiness aid. It is not a legal opinion,
an audit attestation, or a certification. Control ownership, evidence retention,
retention periods, data-subject procedures, and jurisdiction-specific obligations
must be reviewed by the responsible security, privacy, and legal stakeholders.

Status values: **Implemented**, **Partial**, **Pending stakeholder review**.

| Area | Current evidence / implementation | Status | Follow-up |
|---|---|---|---|
| Access control | Authentication, persisted RBAC, owner/workspace scoping, and compliance checks are present in the application. | Partial | Review role assignments, privileged access, periodic access review, and evidence retention. |
| Change and approval control | Production dataset writes use ChangeSets; high-risk actions have approval controls; apply/rollback are audited. | Implemented | Confirm operational approval procedures and reviewer separation. |
| Integrity and auditability | ChangeSet/item SHA-256 commitments, artifact hashes, and audit hash-chain verification are implemented. | Implemented | Define protected audit retention and independent monitoring of verification failures. |
| Data protection | Channel credentials are encrypted at rest; explicit sensitive values are redacted in agent memory/audit paths. | Partial | Complete data inventory, lawful-basis review, encryption/key-management review, and data-subject request procedures. |
| Data retention and deletion | No S28 evidence establishes organization-wide retention schedules or deletion workflows. | Pending stakeholder review | Define retention periods, deletion/backup expiry, and exception handling. |
| Incident response | Structured logging and operational metrics exist. | Partial | Approve incident ownership, escalation, breach assessment, and notification runbooks. |
| Vulnerability management | Bandit and pip-audit run in CI; raw dependency findings are retained. | Partial | Review the ChromaDB exception regularly and track upstream remediation; define scan artifact retention. |
| Network protection | Nginx rate limiting and outbound connector URL checks are implemented. | Partial | Validate proxy/IP configuration and complete an independent penetration test. |
| Availability and recovery | Deployment and disaster-recovery documentation exist. | Partial | Complete Docker runtime, backup-restore, telemetry collector, and alerting validation. |
| Privacy transparency | Product-specific privacy notices and processing records were not assessed in this engineering sprint. | Pending stakeholder review | Review notices, processor agreements, records of processing, and data-subject communication. |

## Review Record

- Engineering implementation snapshot: 2026-09-28.
- Stakeholder owner: **Unassigned**.
- Security/privacy/legal review: **Pending**.
- External audit/certification: **Not performed**.
