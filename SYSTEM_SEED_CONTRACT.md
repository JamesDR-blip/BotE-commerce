# System Seed Contract

## Policy

- `SYSTEM_SEED = YES` only for reference/system data required for persisted application operation.
- `INITIAL_ADMIN = NO`; never create a user, password, token, or admin credential in Alembic.
- `DEMO_SEED = NO`; no sample organization, workspace, project, dataset, channel, workflow, or business records.
- Schema migrations are schema-only. System reference provisioning is an explicit, idempotent operational step after schema validation and before authenticated/governed service is exposed. This separate seed mechanism is a proposed operating contract; it has not been implemented.

## Record decisions

| Record family | Seed decision | Repository evidence | Boundary / unresolved detail |
|---|---|---|---|
| Roles | SYSTEM_SEED | `domain.authorization.RoleName` defines `admin`, `data_engineer`, `reviewer`, `viewer`; persisted RBAC is injected by `services.container.Container`. | Seed stable role names and descriptions; role identifiers/upsert identity should be deterministic or looked up by unique name. Do not create a user or membership. |
| Permissions | SYSTEM_SEED | `services.authorization.ROLE_PERMISSIONS` is the existing reference catalogue of resource/action pairs; persisted `RBACRepository` joins permission rows. | Seed unique `(resource, action)` pairs from the canonical service map. Do not invent extra permission keys. |
| Role-permission links | SYSTEM_SEED | With the persisted repository configured, empty RBAC tables produce no persisted grant; `ROLE_PERMISSIONS` fallback is used only when no repository is configured. | Seed links according to the existing role map. Empty/unseeded catalogue otherwise denies governed permissions. This is required before serving governed access, not a schema-startup prerequisite. |
| Memberships, organizations, users | NO SYSTEM SEED | These are tenant and identity records; no startup seed or first-admin migration is present. | Create only through a separately authorized onboarding/bootstrap operation. The owner/operator and secure initial human identity procedure remain operational prerequisites. |
| Risk policy rows | NO SYSTEM SEED REQUIRED BY CURRENT RUNTIME | `RiskRepository` returns domain defaults (`0.7`, `0.9`) when no row exists. | Do not seed by default. Any mandatory risk threshold policy beyond current fallback is a product decision, not established as runtime-required. |
| Compliance policies | NO SYSTEM SEED REQUIRED BY CURRENT RUNTIME | `ComplianceService` queries organization policy rows and allows when none match; no startup policy row is required. | Do not invent mandatory policy content. Governance owners may separately require policies before tenant use; if so, specify them before provisioning. |
| Quotas | NO SYSTEM SEED REQUIRED | `QuotaService` treats no configured quota as unlimited. | Do not add arbitrary limits. |
| Demo/default workspace and other sample records | FORBIDDEN | No default workspace startup seed; workspace requires an owner. | No demo/sample data in migrations or system seed. |

## Order and validation contract

`PostgreSQL → dedicated Alembic migration job → schema validation → idempotent system-reference seed (roles/permissions/links) → application/API → workers`. Before application traffic, the onboarding process must create the required organization/user/membership through an authorized secure path; this is not `INITIAL_ADMIN` data in Alembic. Seed execution must be repeatable and must not overwrite operator-managed changes outside the system-owned catalogue.

Exact seed command, stable identifiers, and deployment job ownership are not present in the repository and require design before implementation. No seed was executed and no tests were run.

```text
SYSTEM_SEED = YES (RBAC roles, permission catalogue, role-permission links only)
INITIAL_ADMIN = NO
DEMO_SEED = NO
SEED_IMPLEMENTATION = NOT_AUTHORIZED
```
