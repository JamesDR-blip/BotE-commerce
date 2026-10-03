# Blocker Resolution Report — before Phase 5

**Decision: Phase 5 NO-GO.** The initial sandboxed refresh differed from 977; environment diagnosis then isolated the issue and the exact canonical command passed outside the sandbox. This report records both. No architecture migration was performed. No production source code, database code/schema, Alembic migration, runtime configuration, or tests were modified. Focused quality and worker tests were not run; work stopped after baseline verification as instructed.

## 1. Refreshed baseline

- Command: `.\venv\Scripts\python.exe -m pytest -q`
- Environment: Python 3.13.15 (64-bit), Windows 11 build 26200, pytest 9.1.1; executable `D:\Autonomous_E-commerce_Data_Operations_Platform\venv\Scripts\python.exe`.
- Result: **874 passed, 0 failed, 103 errors, 0 skipped, 2 warnings; 99.80 seconds**. The test outcomes sum to 977; this run did not separately report module count.
- Comparison: previously accepted protected baseline is **193 modules / 977 passed**. The refreshed run does not replace that passing baseline.
- Classification of the original mismatch: **environment-related, confirmed**. Representative errors were pytest `tmp_path` setup `PermissionError: [WinError 5] Access is denied` at `C:\Users\Admin\AppData\Local\Temp\pytest-of-JamesDR`; cache warnings also showed denial under the repository `.pytest_cache` path.

### Environment diagnosis and reproduction

- `pytest.ini` sets `testpaths=tests` and `norecursedirs`; it has no `basetemp` or cache override. No `pyproject.toml`, `tox.ini`, root `setup.cfg`, or root `conftest.py` was present; `tests/conftest.py` is the test fixture file.
- `TEMP` and `TMP` both resolve to `C:\Users\Admin\AppData\Local\Temp`; `tempfile.gettempdir()` resolves there when the configured directory exists. When a new `TEMP` directory did not exist, Python fell back to Windows Temp. When pre-created inside the workspace, `tempfile.gettempdir()` resolved there, but sandbox execution still failed to create pytest's child directory.
- Minimal command: `.\venv\Scripts\python.exe -m pytest -q tests/test_api_marketplace.py::test_install_signed_rule_pack_endpoint`. In the sandbox it errored in `tmp_path` setup with `PermissionError: [WinError 5] Access is denied` at the pytest base temp path. Repeating with a pre-created repository-local `TEMP` failed inside the sandbox at that local path. Outside the sandbox, the same existing test passed: **1 passed in 1.78s**.
- Read-only Windows ACL inspection: the Windows Temp root is owned by `JAMESDR\\JamesDR` and grants that identity `FullControl`; `pytest-of-JamesDR` is owned by the same identity with `OWNER RIGHTS FullControl`. `.pytest_cache`, `.pytest-tmp`, and `codex-pytest-temp` are likewise owned by that identity with `OWNER RIGHTS FullControl`. No ACL was changed.
- Root cause: **Codex sandbox filesystem restriction**, not deficient Windows ACL, pytest configuration, test assertion, or application regression. The same default temp path and repository pass outside the sandbox. A repository-local temp path is not a sandbox workaround because the sandbox also denies child creation there.

### Safe remediation and final baseline

No repository test configuration or application configuration was changed. No external ACL change is required. The least invasive remediation is to run the unchanged canonical suite in the approved Windows process context that can access the current user's Temp and repository cache paths. Future sandboxed runs require the execution environment to grant pytest write access to those paths or a supported isolated path. Do not weaken tests or change ACLs to hide the issue.

- Final canonical command (unchanged): `.\venv\Scripts\python.exe -m pytest -q`
- Execution: outside the sandbox, using existing Windows Temp; no `TEMP`/`TMP` or pytest options were changed for this run.
- Final result: **977 passed, 0 failed, 0 errors, 0 skipped, 0 warnings reported; 64.81 seconds**.
- Module comparison: **193 modules / 977 passed — BASELINE RECONFIRMED**. Prior S28 records reported 3 warnings; this latest command produced no warnings summary.

## 2. Quality parity status: PARTIAL

Prior repository inspection identified the runtime path as API `/validate` or `/validations` → `application.quality.QualityService` → planner/`execution.capabilities.CapabilityExecutionService` → clean, validate, and QA capabilities → result, trace, persistence, and report. The registry loads plugins before built-in `validators/` fallback; direct `/clean` and `/extract` retain `DataOperationsService` coupling. `DataHealthService` is a distinct use case.

Existing relevant tests include `test_quality_service.py`, `test_api_endpoints.py::test_validate_uses_real_capability_pipeline`, `test_validation_capability.py`, `test_validation_capability_integration.py`, `test_real_capability_chain.py`, `test_cleaning_capability.py`, `test_data_operations.py`, `test_clean_extract_pipeline.py`, `test_plugins.py`, `test_rule_engine.py`, and data-health tests. These tests were not rerun in this blocker phase. They do not establish every category's plugin precedence, clean/validate/QA parity, error mapping, report content, ordering, or trace parity.

**Remaining risk/action:** focused tests for API and workflow consumers, plugin-first/fallback precedence, categories, errors, reports, and traces are required after the baseline is reproducible. No production behavior should be altered to satisfy characterization tests.

## 3. Worker recovery status: PARTIAL / BLOCKED

Repository code previously inspected: `WorkflowExecutionWorker.run` claims the DB execution, returns when `claim_running` yields `None`, otherwise calls `WorkflowEngine.execute_existing` and records caught exceptions as failure. The Redis consumer recovers idle pending messages with `XAUTOCLAIM` and acknowledges after the worker returns. If a process dies after the DB claim changes `QUEUED → RUNNING` and before terminal persistence, replay may fail to claim and then be acknowledged. No stale-`RUNNING` reconciler was found in the inspected repository.

Existing `test_workflow_execution_worker.py`, `test_workflow_execution_async_state.py`, and `test_redis_workflow_execution_queue.py` do not prove process-death recovery at that exact point. This phase stopped before adding/running the requested focused test.

**Remaining risk/action:** baseline is reconfirmed, but this task explicitly stops after baseline verification. A focused lifecycle test for claim, process death, replay, terminal persistence and ack behavior remains future work. Document the gap; do not redesign recovery here.

## 4. Database lifecycle status: PARTIAL / BLOCKED

Prior repository evidence: `database.models.make_session_factory` unconditionally invokes `Base.metadata.create_all`; `services.container.Container` calls it; API startup via `api.main.create_app` and worker startup via `worker.create_workflow_consumer` build that container. Thus runtime `create_all()` is production-reachable. Alembic is configured against `database/migrations`, has one current head `20260928_01`, and deployment documentation directs operators to `alembic upgrade head`. Docker startup itself does not run Alembic. Test modules also create isolated metadata directly.

The repository does not establish actual deployed database starting states or prove safety for fresh, upgraded, or partially bootstrapped databases. `create_all()` does not apply column alterations or stamp Alembic state. No safety is inferred. The runbook had named `20260923_01`; read-only `alembic heads` confirmed `20260928_01`, and the stale documentation reference was corrected. No migration history changed.

**Remaining risk/action:** define supported fresh/upgraded/partial states, confirm deployment sequence and backup/restore expectations, and validate Alembic fresh and predecessor upgrades plus API/worker startup. No database code or migration history changed.

## 5. Compatibility status: PARTIAL

Classification based only on repository evidence:

| Surface | Classification | Evidence / limit |
|---|---|---|
| Root `dashboard.py` | **ACTIVE** | Docker/Compose/README launcher; delegates to `app.dashboard`. |
| `app.dashboard` / `app.api_client` | **ACTIVE** | UI uses HTTP client; `test_dashboard_client.py` covers mocked client behavior, not full rendered/deployed E2E. |
| Root `main.py` | **LEGACY BUT PROTECTED** | Compatibility launcher delegating to `app.main`, documented by README. |
| `models/database.py`, `models/domain.py`, `api/schemas.py` | **LEGACY BUT PROTECTED** | Re-export compatibility modules; internal consumers do not establish external absence. |
| `ai/`, `controllers/`, `views/` empty package scaffolding | **EXTERNAL UNKNOWN** | Inspected packages have no in-repository runtime/test consumers; external imports cannot be ruled out. Not safe to delete based on this scan. |
| `agents/` and `application/copilot/` | **ACTIVE** | Container and API wiring; Copilot provider can be optional. Provider-connected behavior was not tested in this phase. |
| Any surface marked **PROVEN INTERNAL ONLY** or **SAFE TO DEPRECATE** | **None established** | Absence of internal references is insufficient evidence for either status. |

**Remaining risk/action:** preserve entrypoints and shims; repository-only evidence cannot establish external usage or deprecation safety. Provider-connected behavior and dashboard end-to-end remain unverified.

## 6. scikit-learn status: PARTIAL

Prior import/call-site inspection found scikit-learn usage in `domain/quality/anomalies.py`, importing `sklearn.ensemble.IsolationForest`. The function `detect_anomalies` is called by QAAgent; its anomaly row indices feed quarantine behavior and can affect quality output. Its business responsibility therefore belongs to quality. No persisted estimator/model artifact was identified in the inspected path; outputs are used as runtime anomaly indices rather than a serialized fitted estimator. This phase did not rerun or add tests to establish exact serialization/result contracts.

Relevant tests include QA/quality and capability tests, but exact seed/threshold inputs, output indices, downstream quarantine, score/report effects and any persistence boundary are not proven as a parity suite.

**Required parity before relocation:** pin representative DataFrame inputs, random seed and estimator parameters, exact anomalous row indices, quarantined output, resulting score/report fields, and persistence/serialization behavior for any consumer that stores the result. Do not relocate the implementation now.

## 7. Remaining blockers

1. Baseline environment issue is diagnosed and the accepted 977-pass baseline is reconfirmed outside the sandbox; future sandbox runs still need an allowed temp/cache path.
2. Quality behavior parity across all listed paths/categories remains partial.
3. Worker crash-after-claim and stale-`RUNNING` recovery is untested and may be a real operational gap.
4. Database starting-state safety and the production `create_all()` / Alembic policy remain unproven.
5. External compatibility consumers and provider-connected AI behavior remain unknown.
6. scikit-learn numerical/output parity is not established.
7. Phases 0–4 implementation/gates remain unexecuted; no test pass alone satisfies Phase 5 entry.

## 8. Updated Phase 5 entry decision

**NO-GO.** The baseline is reconfirmed, but quality and worker parity tests were not run in this task, and database lifecycle, compatibility/provider consumers, and scikit-learn parity remain unresolved. Passing the baseline alone does not satisfy Phase 5 entry. Resolve those blockers in separately authorized work, then complete the exact cumulative entry criteria in `MIGRATION_PLAN.md` and `DISCOVERY_REVIEW.md`.

No migration is authorized or started by this report.

## BLOCKER RESOLUTION ROUND 2 — EVIDENCE ONLY (2026-09-29)

This section supersedes earlier statements that focused quality/worker checks had not been run. Phase 5 remains **NO-GO**. This pass changed documentation only; source, tests, migrations, runtime configuration, schemas, dependencies, and test selection were not changed.

### Verification performed

The accepted baseline remains **193 modules / 977 passed**, canonical command `.\venv\Scripts\python.exe -m pytest -q`, completed outside the sandbox in 64.81s. It was not rerun in this evidence round. Focused tests covering API quality, capabilities, plugins/rules, data health, workflows, worker/queues, traces and persistence completed **114 passed in 10.02s**. Exact command:

```powershell
.\venv\Scripts\python.exe -m pytest -q tests/test_api_endpoints.py tests/test_quality_service.py tests/test_validation_capability.py tests/test_validation_capability_integration.py tests/test_real_capability_chain.py tests/test_cleaning_capability.py tests/test_data_operations.py tests/test_clean_extract_pipeline.py tests/test_plugins.py tests/test_rule_engine.py tests/test_validation_services.py tests/test_data_health_service.py tests/test_data_health_domain.py tests/test_s15_data_health_api.py tests/test_ai_agents.py tests/test_capability_execution_service.py tests/test_capability_executor_trace.py tests/test_workflow_runtime_service.py tests/test_workflow_engine.py tests/test_workflow_execution_worker.py tests/test_workflow_execution_async_state.py tests/test_redis_workflow_execution_queue.py tests/test_workflow_engine_version_snapshot.py tests/test_workflow_engine_trace_persistence.py tests/test_workflow_engine_full_persistence.py tests/test_workflow_engine_failure_persistence.py tests/test_api_workflow_execution.py tests/test_studio_workflow_real_capability.py
```

Passing tests establish tested cases only. In particular, worker tests use a fake engine/execution in the representative worker module; they do not prove real-quality execution in a worker or process-death recovery.

### Quality path and parity

| Path | Entry / use case | Capabilities, validator, rules | Error, report, trace and persistence behavior | Coverage and parity result |
|---|---|---|---|---|
| Direct upload API | `api/routes/data.py` `/validate`, `/validations` → `application.quality.QualityService.validate` | Requirement/planning requests `data.qa`; executor dispatches planned clean → validate → QA. `ValidationCapability` uses `ValidationService`, category `ValidatorRegistry`, and `RuleRetrieverAgent`/YAML `RuleRepository`; QA uses `QAAgent`, `HealthScoreService`, and anomaly detection. | Route maps invalid value/request errors to 422 and unexpected errors to 500. Service persists execution, success trace, result, issue logs and XLSX/JSON/HTML/PDF report records. On capability failure it marks failed/rethrows but does not persist attached partial trace. Cache is checked after execution; a hit can return an older summary/ID after current work, without saving current result/report. | `test_api_endpoints.py::test_validate_uses_real_capability_pipeline`, API and quality service tests passed. Representative path proven; cache, partial-failure trace and all report/error cases are not parity-proven. |
| Direct capability execution | `CapabilityExecutionService.execute_plan` / real capability tests | Same registered clean/validate/QA implementations; category validation delegates to `ValidationService`; registry discovers plugins before `validators/` and first category registration wins. Rules come from configured YAML through `RuleRetrieverAgent`; semantic rule search is not executable validation rules. | Returns capability outputs/traces; does not itself provide direct API upload error mapping, report generation, cache semantics or complete direct `ExecutionRecord`/`ReportRecord` lifecycle. | `test_real_capability_chain.py`, capability tests and integration tests passed. Component behavior is not equivalent to the API use case. |
| Direct clean API | `/clean` → `DataOperationsService.clean` | Same cleaning service is wrapped by `CleaningCapability`; no validate/QA capability is invoked. | Returns a preview capped at 100 rows; not the quality report/persistence path. | Data operation and clean/extract tests passed. Intentionally narrower operation, not equivalent to `/validate`. |
| Workflow synchronous | `/workflows/{id}/execute` → `WorkflowRuntimeService` → `WorkflowEngine` with persisted version plan | Authored/snapshotted plan determines capabilities; workflow is not automatically the `QualityService` chain. Validation uses the same capability/validator path when selected. | Persists `WorkflowExecutionRecord`, step outputs and workflow traces; failure handling persists failed state and attached trace. Does not invoke direct `ReportAgent` or write direct `ValidationLogRecord`/`ReportRecord` by default. API returns synchronous result. | Runtime/engine and real studio chain tests passed. Real tested chain is clean+validate, not full QA/report parity. |
| Workflow worker | Async API queues execution ID; worker claims it and invokes `execute_existing` on same engine and pinned plan | Same capability dispatch and validation path as sync for the same plan/version. Worker tests do not prove a real quality plan end to end. | Same workflow records/traces/results as engine sync, but API returns queued ID/state and later status polling; transport ack/recovery is additional behavior. Direct QualityService reports/log records are not implied. | Queue, async state and worker tests passed; representative worker test uses fakes. Real worker quality parity remains unproven. |
| Plugin/category validation | `ValidatorRegistry` called by `ValidationService`/`ValidationCapability` | Discovers plugins before built-in `validators/`; first category registration wins. `plugins.fashion.validator` is active; `validators.fashion` re-exports it. Cosmetics and HomeAppliances fallbacks remain active. Fashion applies YAML rules; Cosmetics/HomeAppliances receive `RuleSet` but use hard-coded checks and ignore it. | Category-specific issues/autofixes feed result. `ValidationService` partitions rows as `frame.iloc[index::4]`, so issue ordering follows stripe order rather than original row order. | Registry/rule/Fashion tests passed. No complete all-category/error/order/autofix parity suite; category semantics are intentionally distinct. |
| Persisted data health | `DataHealthService`, exposed by health metrics/diagnostics and Copilot consumers | Reads dataset profile plus latest completed direct `ExecutionRecord`, score and validation logs; not a validator/capability path and has no independent rule source. | Read-only aggregation; does not create validation reports/traces or run validation. Upload does not pass `dataset_id`; workflow uses a separate execution repository, so linkage is not demonstrated. | Data-health tests passed. Whether upload/workflow results should feed it is **UNRESOLVED** and needs product/data-owner decision. |

**Quality parity: PARTIALLY RESOLVED.** Owners and runtime paths are evidenced, but API, workflow, capability and worker paths have different validation, reporting, trace and persistence envelopes. Establish intended shared contracts and test them before unifying or moving behavior. Preserve direct-clean and category-specific semantics.

### Workflow sync/worker parity

Normal production wiring gives sync and async execution the persisted, pinned workflow-version plan and the same `WorkflowEngine.execute_existing` implementation. `WorkflowRuntimeService` performs owner/scope, authorization, compliance, quota and risk/approval gates before either inline execution or dispatch. The worker claims `QUEUED → RUNNING`, executes the stored plan and persists completion/failure. The queue transports execution IDs; the database record is authoritative. The worker does not repeat API-time gates. Whether policy must be revalidated at delayed execution remains an unresolved product/security decision. A legacy fallback in partially wired/test containers calls `engine.execute()` and resolves the active version; preserve until callers are bounded.

| Concern | Evidence | Status |
|---|---|---|
| Version and capability dispatch | Same pinned version and engine path in fully wired production composition; plan validation and capability dispatch shared. | Equivalent in normal path; fallback differs. |
| Validation/business errors | Engine catches capability exceptions, persists FAILED state and attached trace; synchronous response carries terminal execution. Worker sees normal engine return and queue acknowledges; outer worker exceptions are separately failed. | Business execution shared; exact response/error envelope parity unproven. |
| Retry and terminal states | No execution retry. Redis may reclaim idle pending messages; DB claim accepts only QUEUED. | Recovery semantics differ; crash gap below is confirmed. |
| Reports and persistence | Workflow state/output/traces; no direct quality report generator or validation log/report records by default. | Workflow-specific persistence is current behavior; cross-path reporting contract unresolved. |
| Delivery | Sync waits and returns result; async returns ID/state for polling. Redis ACK follows normal worker return. | Intentional lifecycle difference. |

### Worker failure recovery

**UNRESOLVED — confirmed runtime reliability blocker.** Worker claims an execution by moving it to RUNNING before engine execution. Redis pending-message recovery uses `XAUTOCLAIM` for idle messages, but does not change database execution state. If the process dies after the DB claim and before terminal persistence, redelivery calls `claim_running`; the queued-only claim returns no execution. Worker returns normally and consumer ACKs the message. The row can remain RUNNING indefinitely. No execution lease, heartbeat, database visibility timeout, stale-RUNNING detector, reconciliation process or execution retry/requeue was found. Tests cover failed claims, consumer ACK and pending recovery separately, not this crash window. Partial outputs/traces may make replay nontrivial.

Affected: workflow execution repository/model, `WorkflowExecutionWorker`, Redis consumer/queue, engine terminal persistence and operator recovery. Risk: stuck/lost workflows, ambiguous partial outputs and no idempotent replay guarantee. Required decision: choose lease/retry/reconciliation/idempotency policy, including partial side effects and max attempts. Migration consequence: no worker/queue/execution structural migration until a crash-window test and operational recovery policy pass. No recovery mechanism was implemented.

### Database lifecycle

`database.models.make_session_factory(url)` constructs the engine/session factory and unconditionally calls `Base.metadata.create_all`. `services.container.Container` calls it; API (`api.main`) and `worker.py` both build the container, so production startup can reach `create_all`. No environment guard limits this to tests/development. Production Compose launches API and worker; deployment runbook separately directs `alembic upgrade head`; container startup does not invoke Alembic. Alembic has one head, `20260928_01`, and targets the same metadata. `create_all` creates absent tables but does not apply alterations or stamp Alembic.

Disposable temporary SQLite evidence (no repository or deployed DB touched): (1) empty DB → `alembic upgrade head` failed with `NoSuchTableError: datasets` at `d14c1f2a9b31_add_dataset_storage_key.py:22`; no repository migration creates `datasets`; (2) fresh `make_session_factory`/`create_all` succeeded with 31 tables, then `alembic upgrade head` failed at `7757af5afe0a_add_workspace_ownership.py:28` with SQLite `CircularDependencyError` while batch-altering `workspaces`. This establishes those outcomes for SQLite only. No Alembic upgrade test or predecessor-state upgrade coverage was found. Neither tested fresh ordering is proven to work. API/worker startup against an Alembic-managed state was not validated because a clean Alembic state could not be built. Backup/restore is documented but no restore rehearsal/test was found.

**UNRESOLVED — critical blocker.** Production reachability of `create_all` is confirmed; authoritative production policy and supported starting states are not. Tested fresh SQLite paths fail. Required evidence/decisions: authoritative schema mechanism and startup responsibilities; supported engines/revision states; fresh, predecessor-upgrade and partial-state behavior; schema equivalence; API+worker startup; tested backup/restore and recovery point. Consequence: do not change startup/schema ownership or begin schema-affecting migration until these gates pass. Do not remove `create_all` or alter Alembic in this phase.

### Compatibility and external consumers

| Surface | Classification | Evidence / limit |
|---|---|---|
| `api.main`, documented HTTP/OpenAPI endpoints/aliases | A active; C documented public | Docker/API entrypoint and API docs; preserve paths/error/response contracts. |
| Root `dashboard.py` → `app.dashboard` / `app.api_client` | A active; C documented launch | Compose/README launch root script; UI uses HTTP client; tests mock client, not deployed UI E2E. |
| `worker.py` | A active; C deployed launch | Production Compose launches worker; preserve command and queue contract. |
| `plugins/` and `validators/` subtree discovery | A active; C documented integration | Registry uses package discovery and plugin-first precedence; trusted plugin code documented. No packaging `entry_points` mechanism found. |
| `GOOGLE_API_KEY`, `google.genai`, Copilot/agent wiring | A active optional path; C documented provider | Container/agents and docs establish integration; live provider behavior not tested here. |
| root `main.py`, `models/database.py`, `models/domain.py`, `api/schemas.py` | C documented compatibility; B forwarding | README documents compatibility paths. Internal imports cannot prove external absence. |
| `ai/`, `controllers/`, `views/` scaffolding | E unreferenced internally; D external use unknown | No internal runtime/test consumer found in inspected scaffold. This does not prove safe deletion. |

No surface is proven safe to deprecate from repository search alone. Compatibility is **PARTIALLY RESOLVED**; external consumers and live provider contracts remain unresolved. Keep launch/import shims until usage or deprecation is evidenced.

### scikit-learn usage

Only direct source import found: `domain/quality/anomalies.py` lazily imports `sklearn.ensemble.IsolationForest`; `QAAgent` calls `detect_anomalies`. This is quality policy/behavior. Input is pandas DataFrame; code selects numeric columns, drops columns with any nulls, returns empty for fewer than 10 rows or no numeric columns, fills remaining numeric nulls with medians, fits with `contamination="auto"` and `random_state=42`, and returns anomalous DataFrame index labels. QA merges these indices with validation-error rows and uses them for quarantine; reports include anomaly count. No fitted estimator is persisted. Direct execution persists result/log/report artifacts; workflow JSON serialization may stringify outputs, so exact anomaly-set persistence equivalence is not established. QA assumes source-row/index semantics compatible with common RangeIndex inputs.

`test_ai_agents.py` passed but its small-frame case returns no detector anomalies; no dedicated test pins representative outlier indices, threshold, quarantine, score/report effects or cross-version determinism. A manual same-runtime probe (sklearn 1.9.0) returned `[0, 10, 11]` twice for one synthetic input; this proves that probe only, not the allowed `>=1.5,<2` version range. Quality responsibility is **RESOLVED**; numerical reproducibility and adapter boundary are **UNRESOLVED**. Keep current placement; before moving, pin supported-version outputs and downstream behavior.

### Current blocker disposition

| Concern | Status | Evidence | Required decision / migration consequence |
|---|---|---|---|
| Protected baseline | RESOLVED | Prior canonical run: 193 modules / 977 passed, 64.81s; focused selection: 114 passed. | Keep exact baseline as gate. |
| Quality owner and actual path | RESOLVED | Route, QualityService, planner, capability registrations and validator/rule call sites. | Preserve owners; characterize before moving. |
| Quality parity across API/workflow/capability/worker/category/report/trace | PARTIALLY RESOLVED | Paths mapped; 114 pass, but full workflow QA, worker real-quality, all-category and error/report/trace parity absent. | Define intended shared contracts and prove before unifying/moving. |
| DataHealth linkage | UNRESOLVED | Reads dataset-linked direct executions/logs; upload omits dataset_id; workflow has separate repository. | Decide linkage and test it; do not assume either path feeds it. |
| Sync/worker shared engine | PARTIALLY RESOLVED | Same pinned plan/engine in normal production composition; API gates and async delivery differ; real-quality worker path unproven. | Decide delayed authorization contract and characterize fallback/errors. |
| Worker crash recovery | UNRESOLVED | Queued-only claim + Redis ACK after normal return can strand RUNNING execution; no lease/heartbeat/reconciler/retry found. | Define idempotent recovery and test crash window before worker/queue migration. |
| Database lifecycle/bootstrap | UNRESOLVED | `create_all` production-reachable; tested fresh SQLite orders fail; no Alembic upgrade/restore test or supported existing-state evidence. | Decide authority/state matrix; prove bootstrap, upgrade, startup, equivalence and restore before schema/startup migration. |
| Compatibility/external consumers | PARTIALLY RESOLVED | Active launchers/plugin/provider/API surfaces classified; repository scan cannot enumerate external imports. | Preserve shims; obtain consumer/deprecation evidence before moving/removing public paths. |
| sklearn quality behavior | PARTIALLY RESOLVED | Single import/caller mapped; no dedicated output/quarantine/version parity test. | Pin numerical and downstream behavior before moving implementation/dependency. |
| Phase 5 gate | UNRESOLVED — NO-GO | Worker recovery, DB lifecycle, parity and external boundaries remain unresolved. | Do not start Phase 5. |

No production behavior changed and no architecture migration started.

## PHASE 4.5 — RUNTIME CORRECTNESS REMEDIATION (2026-09-29)

Phase 5 remains **NO-GO**. The round-two findings above are the before-remediation evidence. This section records the narrow changes, regression coverage, and residual blockers. No package moves, public-surface removals, dependency changes, or Phase 5 consolidation were made.

### Execution recovery — RESOLVED WITH TERMINAL-FAILURE POLICY

**Evidence before:** a worker durably claimed `QUEUED → RUNNING`; a crash left the Redis stream entry pending. Redelivery called the queued-only database claim, got `None`, returned normally and was ACKed, leaving RUNNING forever. No lease renewal, stale recovery or retry existed. Completion/failure writes did not provide an atomic terminal-state compare-and-set.

**Contract/change:** the Redis consumer renews only its own pending delivery while its handler runs. On Redis pending-message reclamation, the production worker recovery callback conditionally changes a still-RUNNING execution to FAILED, records a recovery error/finished time and emits the existing RUNNING→FAILED state transition. Work is **not automatically replayed** because capability side effects have no general idempotency contract; operators/users must submit a new execution to retry. If recovery persistence fails, the exception prevents ACK, leaving the pending delivery available for another recovery attempt. Repository completion/failure updates are conditional on a nonterminal state, so a terminal record cannot be overwritten by late completion or duplicate recovery.

**Regression coverage:** extended `test_workflow_execution_async_state.py` to prove atomic claim, single recovery failure, duplicate recovery no-op and rejection of late completion; extended `test_redis_workflow_execution_queue.py` to exercise the claim→simulated process death→reclaimed delivery→FAILED persistence→ACK sequence and pending-delivery lease renewal; extended `test_worker_entrypoint.py` to verify production wiring passes the recovery callback.

**Evidence after:** targeted runtime regressions passed; the complete focused blocker selection passed **124 passed in 14.05s**; canonical `.\venv\Scripts\python.exe -m pytest -q` passed **977 in 66.12s**. Test collection remains **193 modules / 977 tests**. Recovery is idempotent at the durable terminal-state transition and does not replay capability work.

**Remaining risk:** Redis lease renewal can be interrupted by an extended process pause or Redis/network outage; after lease expiry, recovery may mark the execution FAILED even if the old process later resumes. Its late terminal write is rejected, but already-issued external side effects cannot be rolled back. This policy favors at-most-once execution and visible terminal failure over automatic replay. There is no automatic retry or independent database reconciliation if a pending Redis message is lost outside Redis's delivery guarantees.

**Phase 5 consequence:** the confirmed stuck-RUNNING crash window is resolved for Redis pending deliveries and covered by regression tests. Worker/queue migration remains NO-GO until the lease assumptions and recovery consequences are accepted operationally and the remaining database gate is resolved.

### Database bootstrap — PARTIALLY RESOLVED

**Evidence before:** development/test `make_session_factory()` created 31 metadata tables; an empty SQLite database followed by Alembic failed at `d14c1f2a9b31` because the additive history assumes a pre-existing `datasets` table and contains no migration creating it. `create_all()` followed by Alembic failed at `7757af5afe0a` because the generated current `workspaces` schema already has later ownership columns/FKs that the older revision attempts to add through SQLite batch alteration; the observed outcome was a `CircularDependencyError`. The Alembic history is an upgrade path over a pre-existing schema, not an empty-database baseline.

**Contract/change:** fresh test/development initialization continues to use `Base.metadata.create_all()` and is tested for immediate first repository query. Production `Container` construction now calls `make_session_factory(create_schema=False, require_current_revision=True)`: it does not mutate schema and fails startup unless the database is stamped at the repository's current Alembic head. API and worker share this `Container` rule. The historical Alembic revisions were not modified.

**Regression coverage:** existing `test_persistence.py` now also verifies fresh development bootstrap, rejection of an unversioned empty production database without table creation, acceptance of a current-head Alembic-managed schema without metadata mutation, a data-bearing upgrade from `20260926_01` to `20260928_01`, and application/worker construction using the production no-create/current-head policy. The upgrade test verifies the ChangeSet integrity backfill on an existing row.

**Evidence after:** all database lifecycle assertions passed within the focused suite (**124 passed overall**); the current-head upgrade test passed; API and worker construction passed against a test database prepared with current metadata and an Alembic head stamp. Full canonical suite passed **977 in 66.12s**. Alembic history remained unchanged.

**Remaining risk:** empty Alembic bootstrap still fails and no full initial-schema revision exists. The passing upgrade covers only the immediately previous head (`20260926_01`), not every historical or real deployment starting state. The startup test's current-head database is constructed from repository metadata and stamped for the test; it does not prove an operator's deployed schema matches metadata. Backup/restore and PostgreSQL startup/upgrade remain untested. Thus production fresh provisioning and broad existing-state upgrades remain unresolved; use of `create_all()` in non-production is explicitly only a fresh bootstrap, not an Alembic upgrade.

**Phase 5 consequence:** database lifecycle is not cleared. No schema migration or Alembic history change is authorized until a supported production fresh-provisioning path, deployed-state matrix, engine-specific upgrade checks, schema verification and backup/restore evidence are approved and proven.

### Quality synchronous/worker parity — RESOLVED FOR ONE REPRESENTATIVE WORKFLOW

**Evidence before:** the same workflow engine implementation existed in both paths, but the worker test used a fake engine; the real capability-chain test exercised inline execution only. Real worker quality behavior, trace/result equality and error parity were unproven.

**Change:** no production behavior change was needed. The regression test uses the actual container, real `data.clean → data.validate` capabilities, Fashion category/rules and a persisted streaming dataset abstraction; it executes the workflow inline and through `WorkflowExecutionWorker` with equivalent DataFrame chunks.

**Regression coverage:** extended the existing `test_studio_workflow_executes_real_capability_chain` case in `test_studio_workflow_real_capability.py` to compare input/output trace JSON, capability order/status, terminal state, persisted outputs and validation-error state/message/trace behavior. It also asserts workflow runs do not create direct `QualityService` execution records; workflow report generation remains intentionally outside the direct quality report lifecycle.

**Evidence after:** the expanded case passes as part of **124 focused passes** and the **977-pass canonical run**. The selected workflow produced equal clean/validation capability traces and outputs in sync and worker execution; both completed. An unsupported category failed with the same persisted error in both paths.

**Remaining risk:** this proves one streaming workflow and one validation failure only. It does not establish parity for direct upload `QualityService`, all plugin/fallback categories, non-streaming JSON DataFrame inputs, report generation, cache behavior, authorization timing or all persistence effects. The absence of direct quality report records on workflow runs is an existing, intentional use-case distinction, not corrected here.

**Phase 5 consequence:** this representative workflow parity criterion is resolved for the covered cases; broad quality/API parity remains partial and must not be generalized from this test.

### Validation and final blocker table

| Blocker | Before | Change / regression test | After | Remaining risk | Phase 5 gate |
|---|---|---|---|---|---|
| Worker crash after claim | RUNNING row could be stranded and Redis pending entry ACKed on redelivery | Redis delivery heartbeat; reclaimed-message recovery callback; atomic fail-if-running and terminal compare-and-set. Covered by existing async-state, Redis queue and worker wiring tests. | Crash window ends in persisted FAILED; duplicate recovery/late completion cannot replace terminal state; 124 focused and 977 full pass. | No auto retry; lease/network pause may classify a resumed job failed; side effects cannot be rolled back. | Resolved for tested Redis delivery path; operational lease assumptions still require acceptance. |
| Fresh test/dev DB | Metadata create_all succeeded, behavior not explicitly specified | Existing persistence test now verifies tables and first query. | Pass. | `create_all` is not an Alembic migration. | Resolved for test/dev bootstrap only. |
| Production startup schema | Runtime always called create_all | Production container disables create_all and checks current Alembic revision; API/worker startup assertions. | Pass against test-stamped current-head SQLite schema. | Actual PostgreSQL/deployment schema and boot sequence unverified. | Partial. |
| Empty Alembic bootstrap | `NoSuchTableError: datasets` at d14; create_all→Alembic fails at 7757 SQLite batch alteration | No unsafe historical migration edits; explicit production schema gate and isolated test/dev create_all contract. | Failure mechanism bounded; no empty Alembic success claimed. | No clean-install Alembic baseline; no deployment-state/restore evidence. | Unresolved; blocks Phase 5. |
| Existing DB upgrade | Starting states unknown | Added actual `20260926_01 → 20260928_01` upgrade regression with ChangeSet data. | Pass for that revision edge on SQLite. | Earlier revisions and production DB engines/states not covered. | Partial. |
| Quality worker parity | Real worker capability behavior unknown | Existing studio-chain test now runs real streaming clean+validate inline and worker, compares result/trace/errors. | Pass for the representative flow. | Direct API/report/cache/all-category parity not proven. | Partial. |
| Protected baseline | 193 modules / 977 pass | Preserved collection size; canonical command unchanged. | **193 modules / 977 passed**, 66.12s; focused **124 passed**, 14.05s. | Environment remains required to grant writable pytest temp/cache access. | Reconfirmed. |

**Final gate: PHASE 5 = NO-GO.** Worker recovery and the selected workflow parity case are proven within their stated bounds; the empty Alembic bootstrap and broad existing production database lifecycle remain unresolved. No architecture migration started.

## PHASE 4.6 — Database bootstrap closure and quality boundary verification (2026-09-29)

**Phase 5 remains NO-GO.** This pass changed documentation only. It did not modify source, tests, migrations, runtime configuration, schema, dependencies, or architecture. The original accepted baseline remains 193 modules / 977 passed.

### Track A — clean Alembic bootstrap: UNRESOLVED

- Exact reproduction: `$env:DATABASE_URL = 'sqlite:///./.phase46-empty.sqlite'; .\\venv\\Scripts\\python.exe -m alembic upgrade head` (PowerShell; the temporary file was removed afterward).
- Exact failure: `database/migrations/versions/d14c1f2a9b31_add_dataset_storage_key.py:22` calls SQLAlchemy inspector `get_columns("datasets")`; SQLite raises `sqlalchemy.exc.NoSuchTableError: datasets`. This is before Alembic reaches head, application startup, session initialization, or a first repository operation.
- Dependency: the chain starts at `0001_persistence`, which creates users, executions, validation_logs, and reports (conditionally); no ancestor migration creates `datasets`. The `d14` migration assumes it already exists. Later `e2f3a4b5c6d7` and `f3a4b5c6d7e8` similarly assume `workflow_executions` and `datasets` tables.
- Classification: migration history is an upgrade chain over an assumed pre-existing application schema, not a self-contained clean-install chain. This is supported by the missing table creator and current tests initializing complete schemas with `Base.metadata.create_all()` before testing selected migration edges. No migration, seed, startup invariant, or session statement causes this first error.
- Engine scope: SQLite reproduces the failure. No PostgreSQL test service/connection was available in this repository run, so PostgreSQL behavior is unverified. The missing relation dependency is not evidence of a SQLite-only defect; production equivalence must not be claimed without a production-compatible run.
- Safety decision: no migration was added or rewritten. The repository has no authoritative historic baseline definition or clean-install revision to establish which omitted pre-existing tables and constraints belong before `0001`; inventing one or making `d14` conditional would mask the missing schema and leave later revisions failing. `create_all()` is not restored or used to bypass Alembic.
- App path: API and worker production containers require the current Alembic revision and do not create schema. Because upgrade fails before head, the supported production startup path cannot be reached from this empty database. The existing `20260926_01 → 20260928_01` test only proves that one selected predecessor edge on metadata-prepared SQLite data works; it is not fresh-bootstrap evidence.
- Before/change/test/after: before: missing schema prerequisite; change: none, since no evidence-safe root correction exists; regression: no success regression test was added because the clean-install contract cannot safely be asserted without an authoritative schema baseline; the exact failing CLI was rerun and existing selected-edge persistence tests still pass. After: the clean run still raises `NoSuchTableError`, no Alembic head is reached, and application startup is not reached. Risk: a clean production database cannot be provisioned by checked-in Alembic history. Required decision: identify/approve the actual pre-Alembic schema baseline and supported provisioning path, then add the requested end-to-end regression on the production-compatible engine. Consequence: blocks Phase 5.

### Track B — quality boundary

| Concern | Evidence and classification | Phase 5 effect |
|---|---|---|
| Direct API report | `/validate` and `/validations` call `QualityService.validate`; it plans `data.qa`, executes capabilities, saves execution context and capability trace, creates JSON/HTML/PDF/XLSX reports through `ReporterAgent`/`ReportAgent`, saves report paths with the execution result, and maps them to per-execution API URLs. `tests/test_api_endpoints.py::test_validate_uses_real_capability_pipeline` exercises the real route and asserts the report map and uncached response. Workflow execution persists workflow outputs and capability traces but has no `ReporterAgent`, report-path contract, or API report URL. This is an API/application result contract, not a workflow-engine contract; absence of workflow reports is an intentional use-case distinction, not proven duplicated generation or an accidental mismatch. Report bytes/format parity is not applicable because the workflow contract does not promise reports. | **NOT A PHASE 5 BLOCKER** for consolidating ownership; preserve the API report contract and its application-level generation/persistence. The report endpoint should continue to resolve the selected execution's stored report path. |
| Cache | Owner: `application.quality.QualityService` consumes `application.cache.Cache`; implementation is `infrastructure.cache.ttl.TTLCache`, wired by `services.container`. Key is SHA-256 of uploaded source bytes + resolved category + rule version. Expiration is TTL using monotonic time; no explicit invalidation exists, and version change changes the key. Workflow/worker execution never uses this cache, so shared cache semantics are not an existing contract. The API cache lookup currently occurs after capability execution, context/trace persistence, and setting the newly created execution COMPLETED; on hit it returns the cached prior summary and skips `save_result` for the newly created row. This means the cache avoids report/result regeneration, not validation execution, and leaves a completed attempt without its own result/report association. | **PARTIALLY RESOLVED.** Sync/worker cache parity is not required by current contracts, so absence of worker cache is not an architectural boundary blocker. Whether each cached request must retain a fully reportable execution record is an unresolved application behavior contract; classify the current orphaned-completed-row effect as a contained correctness/observability risk. Do not move cache ownership or change hit semantics as part of architecture migration until that product/persistence contract is decided. |
| Validator categories | Registry discovers package plugins first and then `validators/`, retaining the first implementation per category. Actual categories are `Cosmetics`, `Fashion`, and `HomeAppliances`. `Fashion` is the plugin validator; `validators/fashion.py` is a compatibility re-export. Fashion consumes the retrieved `RuleSet` through `RuleValidator`; Cosmetics and HomeAppliances perform category-specific checks and currently do not use the passed rule data; HomeAppliances also has title enrichment/autofix. All are selected by the same `ValidationCapability` and called through the same `ValidatorAgent`/`ValidationService` contract, then QA capability forms the common result. The registry test proves exact categories and plugin precedence; validator and rule tests cover their local behavior. Real synchronous/worker end-to-end parity is proven only for the representative Fashion `data.clean → data.validate` flow. | **NOT A PHASE 5 BLOCKER** for boundaries: category-specific implementation is expected and all categories share the same capability input/output/error envelope by static contract. Worker execution behavior for Cosmetics and HomeAppliances is **untested**, not claimed as proven; retain them in place unless a migration slice touches that behavior, and require category cases then. No universal output identity is asserted. |

The review did not prove all-category worker report/cache parity, and does not claim it. The tested API report contract is intentionally distinct from worker workflow output. The remaining cache persistence question is recorded above rather than generalized into a requirement for cache use in workers.

### Verification after this review

- The unprivileged focused attempt encountered the already-diagnosed sandbox `tmp_path` restriction (9 setup errors, 22 tests completed, cache/temp permission warnings); it is not treated as an application failure.
- Focused command in normal Windows filesystem context: `.\\venv\\Scripts\\python.exe -m pytest -q tests/test_api_endpoints.py tests/test_quality_service.py tests/test_plugins.py tests/test_validation_capability.py tests/test_validation_capability_integration.py tests/test_real_capability_chain.py tests/test_studio_workflow_real_capability.py tests/test_persistence.py` — **31 passed in 8.01s**.
- Canonical command in normal Windows filesystem context, unchanged: `.\\venv\\Scripts\\python.exe -m pytest -q` — **977 passed in 68.97s**; baseline remains **193 modules / 977 passed**. No new tests or test selection changes were made.

### Phase 4.6 gate statuses

| Issue | Status | Evidence | Risk / required action | Gate |
|---|---|---|---|---|
| Clean Alembic bootstrap | **UNRESOLVED** | Empty SQLite upgrade deterministically fails at `d14` because `datasets` is absent; later migrations require additional pre-existing tables. | Establish and validate the authoritative clean-install/pre-Alembic schema baseline on supported production DB engine. | Blocks Phase 5. |
| Alembic existing upgrade | **PARTIALLY RESOLVED** | `20260926_01 → 20260928_01` with representative ChangeSet rows passes SQLite regression. | Earlier edges, production engine, deployed start states, backup/restore remain unproven. | Continue blocked. |
| API/workflow report distinction | **NOT A PHASE 5 BLOCKER** | Direct route and real capability test; workflow engine has no report contract. | Preserve direct API report URL/content persistence semantics. | No ownership blocker established. |
| Cache parity | **PARTIALLY RESOLVED** | App/infra cache ownership, key, TTL, lack of explicit invalidation, and call order traced; worker has no cache consumer. | Decide whether cached request attempts require own persisted results; current hit leaves a completed row without result association. | Not a cross-runtime boundary blocker; behavior decision required before cache-specific migration. |
| Validator categories | **PARTIALLY RESOLVED** | Three categories, plugin precedence, shared capability contract and local tests; worker E2E only for Fashion. | Cosmetics and HomeAppliances worker cases remain untested. | No proven architectural correctness divergence; test if later slice changes validator dispatch/execution. |
| Worker crash recovery / representative execution | **RESOLVED within stated coverage** | Prior Phase 4.5 crash recovery regression and Fashion sync/worker real streaming parity; no source change this pass. | Existing Redis lease/side-effect limitations remain documented. | No new blocker identified. |
| Protected suite | **RESOLVED** | Current canonical run: 193 modules / 977 passed, 0 failed/errors/skipped. | Continue using a writable test context. | Baseline preserved. |

**Final Phase 5 decision: NO-GO.** The clean production-compatible database bootstrap is unproven and presently fails on the only available database engine. This alone fails the entry gate. No architecture migration began.

## PHASE 4.7 — MIGRATION HISTORY FORENSICS (2026-09-29)

**Read-only evidence pass; no migration, schema, startup, dependency, or test changes. Phase 5 remains NO-GO.** `alembic heads` reports one head, `20260928_01`. `alembic history --verbose` and the 22 files under `database/migrations/versions` show one connected linear chain, displayed below in ancestry order (not filename/date order):

`0001_persistence → 7757af5afe0a → b05fd7d45c87 → c13a7e91d204 → d14c1f2a9b31 → e2f3a4b5c6d7 → f3a4b5c6d7e8 → 20230912_01 → 20230912_02 → fcbc1a52044c → 20230912_03 → 20230912_04 → 20260914_01 → 20260914_02 → 20260914_03 → 20260916_01 → 20260916_02 → 20260916_03 → 20260916_04 → 20260922_01 → 20260923_01 → 20260926_01 → 20260928_01`.

### Complete revision inventory

“Indexes” lists explicit and column-declared indexes at table level; primary/foreign/unique constraints are summarized by relationship/type. No upgrade revision drops a whole table; table drops occur in downgrade functions as indicated. `b05fd7d45c87` deletes one conditional demo row. `fcbc1a52044c` downgrade is a no-op. No migration seeds reference rows.

| Revision / parent | Purpose; tables created / altered / dropped | Indexes and constraints | Data effect / pre-existing schema assumptions |
|---|---|---|---|
| `0001_persistence` / base | Conditional create: `users`, `executions`, `validation_logs`, `reports`; alternatively alters `executions.user_id`; downgrade drops `users` and removes `executions.user_id` if present. | `ix_users_email`, `ix_users_created_at`; execution indexes on user/category/source_hash/created_at; validation_logs.execution_id index. Email unique; execution.user_id→users; validation_logs/reports→executions. | No seed rows. Explicitly described as adding ownership to an **existing** persistence schema. On empty DB it creates four tables, not the entire application schema; on DB with executions it assumes the rest of execution schema already exists.
| `7757af5afe0a` / `0001_persistence` | `CREATE TABLE IF NOT EXISTS workspaces`, then alter/add `workspaces.owner_id`; no drop in upgrade. Downgrade removes owner field/index/FK. | `ix_workspaces_owner_id`; owner→users FK. | No seed; assumes `users`. Workspaces base table is created here only when missing. Existing workspace shape is assumed compatible with owner change.
| `b05fd7d45c87` / `7757af5afe0a` | Alters `workspaces.owner_id` nullable→not-null. | Existing owner index/FK retained. | Deletes only `workspaces.id='ws-demo'` if its owner is null; no inserted reference rows. Assumes workspaces and owner_id from predecessor. File docstring contains a stale placeholder revision label, but Python revision/down_revision values are valid and Alembic graph resolves.
| `c13a7e91d204` / `b05fd7d45c87` | Creates `agent_memory`; downgrade drops it. | Workspace/user indexes plus composite scope/type/key index; FKs to workspaces/users. | No seed; assumes both referenced tables exist.
| `d14c1f2a9b31` / `c13a7e91d204` | Adds nullable `datasets.storage_key`; downgrade drops it. | No new index/constraint. | No data seed/backfill. **First revision to reference `datasets`**; assumes the table already exists. Inspector fails on an empty DB before it can test/add the column.
| `e2f3a4b5c6d7` / `d14c1f2a9b31` | Adds nullable `workflow_executions.dataset_id`; downgrade removes it. | Dataset FK and `ix_workflow_executions_dataset_id`. | No data seed. Assumes `workflow_executions` and `datasets` exist.
| `f3a4b5c6d7e8` / `e2f3a4b5c6d7` | Adds nullable `executions.dataset_id`; downgrade removes it. | Dataset FK and execution dataset index. | No data seed. Assumes `executions` and `datasets` exist.
| `20230912_01` / `f3a4b5c6d7e8` | Creates `risk_policies`, `approvals`; downgrade drops both. | `approvals.execution_id` index; later revision adds its FK. Risk thresholds have server defaults 0.7/0.9. | No reference row inserted. Assumes predecessor execution/dataset schema indirectly through parent chain.
| `20230912_02` / `20230912_01` | Alters `approvals.execution_id` to add/drop FK. | FK to `workflow_executions`; approval execution index is managed in batch alteration. | No row data. Requires approvals and workflow_executions pre-exist.
| `fcbc1a52044c` / `20230912_02` | Creates `workspaces`; downgrade is `pass` (does not remove it). | Primary key only; no explicit index/FK in this revision. | No seed. `7757af5afe0a` already creates `workspaces` when absent, so the linear chain has a second unconditional workspace create. Under a fresh path it can collide; under a pre-provisioned path the earlier owner alteration is also baseline-dependent. This is additional evidence that the chain requires reconciliation against a defined starting schema, not evidence to guess that schema.
| `20230912_03` / `fcbc1a52044c` | Creates `risk_assessments`; downgrade drops it. | `ix_risk_assessments_execution_id`; FK to `workflow_executions`. | No seed; assumes workflow_executions already exists.
| `20230912_04` / `20230912_03` | Adds non-null `approvals.token_hash` with temporary empty-string default, then removes server default; downgrade drops column. | No index/constraint added. | Existing approval rows receive empty string; no separate data update. Assumes approvals table exists.
| `20260914_01` / `20230912_04` | Creates `changesets`, `changeset_items`; downgrade drops both. | Dataset/execution/workflow FKs; changeset-items FK; indexes on changeset dataset/execution/workflow/status/created_at and item changeset_id. | No seed. Assumes datasets, workflow_executions, workflows exist.
| `20260914_02` / `20260914_01` | Adds `approvals.changeset_id`. | Index and FK to changesets. | No data backfill/default before NOT NULL; assumes approvals rows are compatible (and changesets exist). This is a potential existing-data migration precondition.
| `20260914_03` / `20260914_02` | Creates `data_lineage_events`, `audit_events`; downgrade drops both. | Lineage FKs to datasets/workflow_executions/workflows; audit FKs to workspaces/users and optional workflow executions/changesets; indexes on FK/time/resource fields; audit event_hash unique/indexed. | No seed. Assumes all referenced core and newly migrated tables exist.
| `20260916_01` / `20260914_03` | Creates `channels`; downgrade drops it. | workspace FK; indexes on workspace_id/created_at. | No seed. Assumes workspaces.
| `20260916_02` / `20260916_01` | Creates `sync_jobs`, `sync_attempts`; downgrade drops both. | Job FKs to workspace/dataset/channel; attempt FK to job; indexes on workspace/dataset/channel/status/created_at and attempt job/status/created_at. | No seed. Assumes workspaces, datasets, channels.
| `20260916_03` / `20260916_02` | Creates `channel_mappings`; downgrade drops it. | Channel FK; unique channel/canonical-product pair; indexes on channel/canonical-product/created_at. | No seed. Assumes channels.
| `20260916_04` / `20260916_03` | Creates `organizations`, `roles`, `permissions`, `role_permissions`, `memberships`; alters existing `workspaces.organization_id`. Downgrade drops new tables/field. | Unique role name, permission resource/action, role-permission pair; composite membership uniqueness; FKs to organizations/users/roles/permissions; workspace organization FK/index. | No seed. Assumes users and existing workspaces with expected pre-organization columns.
| `20260922_01` / `20260916_04` | Creates `organization_quotas`; downgrade drops it. | Organization FK/index; uniqueness as declared in migration. | No seed; assumes organizations.
| `20260923_01` / `20260922_01` | Creates `compliance_policies`; downgrade drops it. | Organization FK/index; unique organization/name. | No seed; assumes organizations.
| `20260926_01` / `20260923_01` | Adds `changesets.integrity_hash`, backfills existing rows, then makes it non-null; downgrade drops it. | No new index/constraint. | Data backfill computes hashes from existing ChangeSet fields. Assumes changesets and all selected columns exist; existing records are read and updated.
| `20260928_01` / `20260926_01` | No table/column/index changes; recomputes integrity hashes including item snapshots; downgrade recomputes the previous hash form. | No schema constraints/indexes changed. | Data rewrite of existing changeset integrity_hash values. Assumes changesets and changeset_items plus expected fields exist.

The file names `20230912_*` are not chronological with their checked-in commit dates in September 2026; ancestry above is definitive for ordering. There are **23 revisions** and one head; no parallel Alembic branch exists in the current script directory. Although the revision graph is linear, the two workspace-creation behaviors show the revisions do not establish a single clean-start path as written.

### `datasets` schema sources and classifications

| Source | Classification | Evidence / limit |
|---|---|---|
| `database/models.py::DatasetRecord` and `Base.metadata` | **B — application model only**, not a versioned historical schema specification | Dataset ORM model first appears in Git commit `977fb44` (2026-08-20). The model declares datasets; this does not by itself establish any deployed database schema.
| Historical `database.models.make_session_factory()` | **Strong evidence of historical application bootstrap source** | At Alembic introduction (`192a9ea`, 2026-07-31), the function called `Base.metadata.create_all(engine)` and `services.container` called the factory. `ARCHITECTURE_AUDIT.md` at that commit explicitly describes startup-time `create_all`. That explains how later-added ORM tables could have existed when additive migrations ran, but does not prove any production database was initialized that way.
| Current `make_session_factory()` non-production path | **Application bootstrap for development/test** | Current code still conditionally calls metadata create_all; Phase 4.5 disables it for production. It is not Alembic and does not prove old schema versions.
| `tests/test_persistence.py`, `tests/conftest.py`, other tests | **Test-only schema setup** | Test fixtures use `Base.metadata.create_all()` and selected test schemas. Tests do not establish the production historic baseline.
| Tracked `data_quality.db` | **D — historical/local SQLite artifact** | Git shows it changed alongside model/test development. Read-only schema inspection found `datasets` and `alembic_version=20260928_01`; this reflects a populated current local DB, not an empty-bootstrap recipe or production proof. No row data was inspected.
| SQL bootstrap/seed/init scripts or external schema artifact | **E — undocumented/external assumption not found in repository** | No `.sql` file, Docker init mount, schema bootstrap command, seed script, or deployment migration job was found. The production Compose file starts PostgreSQL, API, worker, dashboard and Redis; it contains no migration service/command or DB init scripts.
| Dataset domain model and API/repository | **Application/domain behavior only** | Domain Dataset has no DDL authority. Repository persists via ORM. No alternate schema declaration found.

Repository scan found no other `CREATE TABLE datasets`, SQL schema file, deleted migration file on available `main`, production provisioning script, or documented external schema package. The PostgreSQL container's empty named volume initializes a database server but does not create application tables.

Migration imports/configuration: `alembic.ini` provides `script_location=database/migrations` and `prepend_sys_path=.` but no active database URL. `database/migrations/env.py` loads `Settings().database_url`, imports `database.models.Base` as `target_metadata`, then runs the revision scripts; it does not call `create_all`. Revision modules import Alembic/SQLAlchemy and do not import application repositories/services or an external schema package. Revision links are encoded in `revision`/`down_revision` values; the current script directory resolves one head.

Source classification summary: ORM/model declarations are **B (application model only)**; test metadata/fixtures are **C**; tracked local SQLite DB and source-control DB snapshots are **D**; no repository external provisioning source was found, so reliance on one would be **E (undocumented)**; no schema source was confirmed **F (dead/unreferenced)**. The historical `create_all` invocation is an active-on-startup application bootstrap in those commits, but is not itself a versioned authoritative DDL artifact.

### Git history and migration model

Available `main` history shows the first Alembic commit `192a9ea` added `0001_persistence.py`, `env.py`, and `alembic.ini`; its migration text/title says it modifies an **existing execution persistence schema**. At that commit the application startup factory called `Base.metadata.create_all()`. Commit `977fb44` later introduced DatasetRecord and updated the tracked local SQLite DB; commit `9a7a57a` added `d14c1f2a9b31` to add `storage_key` to the already-existing datasets table, without a table-creation revision. No migration deletes/renames/squashes are present in reachable `main` history. Later migration commits are additive and chain linearly. This is affirmative evidence that the historical codebase expected a pre-provisioned base schema, most plausibly from application ORM startup, then used Alembic for selected subsequent changes.

**Current migration model classification: B — Alembic starts from a pre-provisioned baseline schema (HIGH confidence for historical intent).** It is not A: empty SQLite fails. There is no affirmative evidence for C (lost/squashed history) or D (multiple histories): current script graph is linear and Git shows no deleted revision in reachable main. The actual baseline DDL and whether production ever followed the app-bootstrap path remain unknown. Current production code/runbook now disables create_all and instructs Alembic-first startup, so the current documented operational path is inconsistent with the historical additive migration assumptions. This classifies current operability as unresolved, not as proof that the chain was deliberately designed for Alembic-from-empty.

History limitations: `git log main` was inspectable, and the local `agents/everyday-stingray` ref showed only the initial migration commit for this path. `git log --all` reported a broken Codex checkpoint ref/bad object; therefore unreachable/pruned commits or remote-only history cannot be ruled out. No remote production database was accessed. `docker-compose.prod.yml` and `docs/production-deployment.md` specify PostgreSQL 16. `docs/operator/database-migration.md` says apply `alembic upgrade head`, while `docs/production-deployment.md` only instructs `docker compose up -d`; no initial schema provisioning command/artifact is documented. Production Compose has no migration service/command or DB init scripts. CI runs SQLite/default tests without a PostgreSQL service. Secrets/environment values were not displayed.

### Required status fields

- **MIGRATION_HISTORY_STATUS:** one linear Alembic graph, 23 revisions, one head `20260928_01`; demonstrably not self-sufficient from empty DB, with repeated workspaces creation assumptions; historical code expects pre-provisioned application schema.
- **AUTHORITATIVE_SCHEMA_SOURCE:** historical startup `Base.metadata.create_all()` is the only repository-evidenced mechanism capable of producing omitted ORM tables before additive migrations; classification is **historical application bootstrap evidence**, not a verified authoritative deployed schema contract. A complete versioned baseline schema artifact is absent.
- **PRODUCTION_SCHEMA_STATUS:** **PRODUCTION SCHEMA STATE = UNVERIFIED**. Production is configured/documented as PostgreSQL 16, but no production connection, schema dump, Alembic current output, deployment log, backup, or operator provisioning record is available.
- **MIGRATION_REPAIR_REQUIRED:** **YES for the currently documented empty-PostgreSQL/Alembic-first path; CONDITIONAL for the historical pre-provisioned-baseline model.** A supported bootstrap operation/path must be supplied before production startup can be considered complete. It is not yet determined whether the proper remedy is restoring a missing historical revision, documenting an external baseline, or another approved process. No repair was made.
- **MIGRATION_REPAIR_CONFIDENCE:** **High** that clean Alembic upgrade lacks required schema (empty SQLite reproduction, source chain, Git history); **medium-high** that historical intent was pre-provisioned schema from ORM startup; **low** confidence about the actual production baseline and what repair is correct. Do not repair until the latter evidence is supplied.

Phase 5 stays **NO-GO**. No full suite was run because this was a read-only forensic/documentation pass; the protected 977-test baseline is carried forward, not newly re-verified here.

## PHASE 4.8 — PRODUCTION BASELINE & PROVISIONING EVIDENCE (2026-09-29)

**No migration repair. No production startup/deployment/test/schema changes.** This pass inspected repository/deployment sources and local tool availability only. No secrets or `.env` values were printed.

### Production contract fields

- **PRODUCTION_DB_ENGINE:** PostgreSQL, specified by `docker-compose.prod.yml` (`postgres:16-alpine`) and `docs/production-deployment.md`.
- **PRODUCTION_DB_VERSION:** 16 (repository target; actual deployed server version is not verified).
- **PRODUCTION_SCHEMA_PROVISIONING_METHOD:** **Unknown for production.** No schema init SQL, Docker init mount, seed/bootstrap script, or baseline artifact exists in the repository. Historical code called application metadata `create_all()` at startup, which could create missing tables, but no deployment record proves production used it. Current production code disables it.
- **PRODUCTION_MIGRATION_METHOD:** `docs/operator/database-migration.md` directs operators to execute `alembic upgrade head` through the deployment environment. There is no Compose migration service, container command, entrypoint step, or CI deployment job that runs Alembic.
- **PRODUCTION_STARTUP_ORDER:** Compose starts PostgreSQL and Redis; API, worker, and dashboard depend on their health. API starts Uvicorn `api.main:create_app`; worker runs `python worker.py`; both construct the shared container and current production policy requires Alembic at head with metadata creation disabled. Nginx waits for API health and dashboard startup. Compose contains no schema provisioning/migration stage before API/worker.
- Environment variable names observed (names only): `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`; also Redis and observability variables. No values were printed.
- Readiness checks: PostgreSQL uses `pg_isready`; API Compose health checks `/livez`; Nginx checks `/healthz`. Readiness verifies service availability, not schema creation.
- Backup/restore: operator migration runbook says to confirm a valid backup through the deployment environment. Rollback docs require identifying schema compatibility but provide no backup command, artifact, retention metadata, or restore rehearsal. No backup/restore artifact was found in the repository.

### Historical provisioning candidates

| Candidate | Evidence, callers, deployment reachability | Assessment |
|---|---|---|
| A. `Base.metadata.create_all()` | At Git commit `192a9ea` (first Alembic files), `database/models.py::make_session_factory()` called `Base.metadata.create_all(engine)`, `services.container.Container` called that factory, and `api.main.create_app()` constructed `Container`. Later history added `DatasetRecord` in `977fb44` while that same factory still called create_all. This code was on the API startup path; it was technically production-reachable in deployments using that API version/config. That demonstrates a historical application bootstrap mechanism, not proof that production actually used it or that it was the sole production schema source. | **Plausible historical source; actual production use UNKNOWN.** Strong code evidence, no deployment logs/state evidence. Not authoritative as a versioned baseline.
| B. Alembic | Alembic was introduced by `192a9ea` as “user ownership to existing execution persistence schema.” Root `0001_persistence` conditionally adds/creates part of that schema; later revisions expect other tables. `d14` changes an existing datasets table. Runbook says operators use `alembic upgrade head`; no deployment step executes it. | **Historical additive migration mechanism established; production execution UNKNOWN.** Not self-sufficient from empty DB.
| C. SQL/bootstrap scripts | Repository file inventory and text search found no application schema `.sql`, entrypoint init script, Compose `docker-entrypoint-initdb.d` mount, or seed script. | **NOT FOUND.**
| D. Manually provisioned schema | No operator baseline DDL, `psql` provisioning steps, schema dump, or production database record found. | **NOT FOUND in repository; external action cannot be ruled out.**
| E. External infrastructure | Production docs permit CI/CD secret injection/container orchestration and Compose provisions a PostgreSQL service/volume, but neither provides evidence of who creates application tables. No Terraform/Helm/cloud database schema provisioning artifact is checked in. | **External baseline is possible but undocumented; UNKNOWN.**
| F. Other/unknown | Current tracked `data_quality.db` is SQLite and has a full current schema plus `alembic_version=20260928_01`. Git history shows the DB binary changed during local model development. It contains current tables, not an empty PostgreSQL bootstrap sequence or verified historic PostgreSQL baseline. | **INSUFFICIENT** as production evidence; historical local artifact only.

No source has been promoted to “authoritative production baseline.” The historical `create_all()` path explains how `datasets` could exist before an additive revision, but does not establish production usage or a stable schema snapshot.

### Current deployment flow assessment

The operator runbook’s `alembic upgrade head` instruction and the deployment guide’s `docker compose ... up -d` steps are **D. incomplete documentation**, with potentially complementary intended steps. They can be complementary only if an operator first makes PostgreSQL available, runs Alembic from a separately prepared environment, then starts API/worker. The repository specifies no exact command/container, no `up db` then migration sequence, and no migration job. The documented Compose startup alone waits for database health and starts the app services; it does not run Alembic. Current application startup then rejects a database not already at head. For an empty Compose PostgreSQL volume the documented steps therefore lack a working schema path. Do not infer operator behavior not present in evidence.

### PostgreSQL 16 verification

**POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE.** `docker`, `psql`, and `pg_isready` executables were unavailable in this environment. No authorized isolated PostgreSQL 16 service/connection was identified. No PostgreSQL runtime attempt was made, and SQLite results were not substituted for PostgreSQL evidence. Therefore these tests were not run: empty PostgreSQL → Alembic head; a verified historical baseline → head; API and worker startup; representative PostgreSQL operation. No test/configuration changes were made.

### Baseline artifacts

**AUTHORITATIVE BASELINE ARTIFACT = INSUFFICIENT.** The tracked SQLite `data_quality.db` is present and includes datasets plus a current revision marker; it is not PostgreSQL, not an empty bootstrap recipe, and not a documented historical release baseline. No schema dump, PostgreSQL backup metadata, deployment artifact, migration snapshot, initialization SQL, or CI database bootstrap artifact was found. The Git history provides source chronology but no trustworthy production schema state.

### Alembic takeover feasibility

| Target | Decision | Evidence |
|---|---|---|
| A. Empty PostgreSQL database | **NO** for the current chain as an authoritative empty-database initializer | No revision creates `datasets`; `d14` assumes it. The root and later chain also assume `workflow_executions`, and revisions contain repeat workspace-creation assumptions. Exact runtime behavior on PostgreSQL was not tested, but static DDL establishes that this chain has no complete table-creation path for an empty DB. |
| B. Existing production baseline | **UNKNOWN** | No actual production schema, `alembic current`, schema dump, operator record, or verified baseline artifact. Existing SQLite metadata-prepared upgrade test does not establish production state. |
| C. Future upgrades | **UNKNOWN** generally; one narrow edge has test evidence | SQLite test evidence covers `20260926_01 → 20260928_01` only. No PostgreSQL upgrade, full prior chain, baseline validation, backup/restore, or production start state is verified. |

### Required status fields and decision

- **PRODUCTION_DB_ENGINE:** PostgreSQL.
- **PRODUCTION_DB_VERSION:** 16 intended; deployed runtime version unverified.
- **PRODUCTION_SCHEMA_PROVISIONING_METHOD:** unknown; historical ORM `create_all()` is plausible but actual production use is unproven.
- **PRODUCTION_SCHEMA_BASELINE:** **INSUFFICIENT**; no authoritative PostgreSQL baseline artifact or state found.
- **PRODUCTION_SCHEMA_BASELINE_CONFIDENCE:** **LOW** for any claim about production. High confidence only that historical code exposed `create_all()` and Alembic revisions depend on pre-existing tables.
- **POSTGRESQL_RUNTIME_VERIFICATION:** **UNAVAILABLE**.
- **ALEMBIC_TAKEOVER_STATUS:** **NO** from empty DB; **UNKNOWN** for existing production baseline and general future upgrades.
- **MIGRATION_REPAIR_STATUS:** **BLOCKED**. Repair approach cannot be selected without authoritative baseline/provisioning evidence. No repair was made.
- **PHASE_5_GATE:** **NO-GO**. Production schema state is unverified; clean provisioning is not demonstrated; PostgreSQL runtime verification is unavailable.

No migration repair is authorized or started. Keep Phase 5 blocked until a trusted PostgreSQL baseline/provisioning artifact or operator record is provided and the supported upgrade/startup path is verified in an isolated PostgreSQL 16 environment.

## PHASE 4.9 — EXTERNAL EVIDENCE GATE

Repository-side forensics are closed. No further repository-only inference is being made. No source, test, migration, schema, startup, or deployment file was changed.

### Evidence request

Provide one authoritative production-equivalent database artifact:

- Isolated PostgreSQL 16 staging database representing the production schema.
- Schema-only PostgreSQL dump.
- Approved production schema snapshot.
- Authoritative provisioning artifact.
- Equivalent deployment database artifact.

The artifact must identify engine/version, capture date, deployment/application version, schema revision if known, and whether it represents pre-migration or current production state. Exclude credentials and application row data unless separately required and approved. Do not substitute ORM metadata or tracked SQLite data.

### Verification checklist once available

1. In an isolated PostgreSQL 16 environment, verify an empty database through the documented initial provisioning and Alembic process; record exact revision and failures.
2. Verify the authoritative existing schema without changing production; record its Alembic version and compare required tables, columns, indexes, constraints, and migration assumptions.
3. Run the Alembic upgrade from that existing baseline in isolation; record pre/post revision and schema differences.
4. Start the API against the resulting schema.
5. Start the worker against the same schema.
6. Perform a representative database write/read and verify persistence.
7. Verify backup/restore assumptions only where an authoritative procedure or artifact exists; record unverified parts.

### Questions for the evidence owner

- What creates the initial production schema?
- At what point does Alembic become authoritative?
- What revision represents the baseline?
- Can Alembic upgrade an existing production baseline?
- Can a new environment reproduce the same schema?
- What is the supported deployment order for PostgreSQL provisioning, migration, API startup, and worker startup?

### Current decision

- **PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
- **POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
- **MIGRATION_REPAIR = BLOCKED**
- **PHASE_5 = NO-GO**

Do not select or implement a migration repair until an authoritative artifact and answers to these questions are available. This gate does not authorize migration work.

## EXTERNAL EVIDENCE ACQUISITION — ENVIRONMENT CHECK

Availability-only result: Docker, Docker Compose, PostgreSQL client/server utilities (`psql`, `pg_isready`, `postgres`, `pg_ctl`, `createdb`) were unavailable as commands; no PostgreSQL process or Windows service was present. The repository declares a PostgreSQL 16 Compose service, but no local Compose runtime is available to start an isolated instance. CI has no PostgreSQL service/database declaration. Development configuration defaults to SQLite. No staging PostgreSQL configuration was identified. No connection was attempted and no SQLite substitution was made.

**POSTGRESQL_RUNTIME_VERIFICATION = UNAVAILABLE**
**BACKUP_RESTORE_VERIFICATION = UNAVAILABLE**
**EMPTY_DATABASE_ALEMBIC_BOOTSTRAP = UNKNOWN (not run on PostgreSQL)**
**EXISTING_BASELINE_ALEMBIC_UPGRADE = UNKNOWN**
**API_STARTUP = UNKNOWN on PostgreSQL**
**WORKER_STARTUP = UNKNOWN on PostgreSQL**
**PRODUCTION_SCHEMA_BASELINE = UNKNOWN**
**ALEMBIC_TAKEOVER = UNKNOWN for existing baseline; empty-database path remains unsupported by repository evidence**
**MIGRATION_REPAIR = BLOCKED**
**PHASE_5 = NO-GO**

### External evidence request — minimum required

Provide exactly one of:

A. A PostgreSQL 16 schema-only dump from the authoritative environment; or
B. Access to an isolated PostgreSQL 16 staging database representing the production baseline; or
C. The authoritative provisioning artifact that creates the production schema.

Include metadata only: PostgreSQL version; schema baseline date/revision; provisioning method; required extensions; Alembic migration state; and whether the source represents production, staging, or development. No credentials or secrets are required. Do not send application row data for a schema-only request.

After receipt, use only an isolated disposable PostgreSQL 16 database to check empty bootstrap, existing-baseline upgrade, API and worker startup, representative write/read, schema objects, and documented backup/restore assumptions. Do not connect to production or alter shared databases. Stop this phase until the external evidence is provided.
