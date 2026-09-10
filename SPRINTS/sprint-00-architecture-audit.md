# SPRINT 00: Architecture Audit & Baseline Refactor

## Status
Completed

## Objective
Establish architectural baseline, audit existing technical debt, introduce application factory and explicit composition root (services/container.py), and define safe boundary rules.

## Deliverables
- Comprehensive architecture audit document (ARCHITECTURE_AUDIT.md).
- Application factory pattern for FastAPI (pi/main.py:create_app).
- Composition root (services/container.py) eliminating global mutable singletons.
- Initial regression test harness.
