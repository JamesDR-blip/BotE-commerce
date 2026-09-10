# AFTER ANALYSIS PROMPT

The implementation plan has been reviewed and approved.

Proceed to implementation following these rules:

1. Follow the approved plan:
   - Implement only the proposed changes.
   - Do not redesign or refactor code outside the scope of the plan.

2. Preserve Clean Architecture + DDD boundaries:
   - Domain layer must remain pure and free from framework/database/HTTP imports.
   - Application layer orchestrates domain services and repositories.
   - Execution layer manages workflow state, capability execution, and tracing.
   - Infrastructure layer implements technical adapters (persistence, cache, upload).
   - Presentation layer (FastAPI routes / Streamlit) delegates to application services.

3. Follow Engineering Rules:
   - Implement the smallest coherent change.
   - Reuse existing services and capabilities where possible.
   - Maintain backward compatibility of existing endpoints and contracts.
   - Never use eval(), exec(), unsafe YAML loading, or unvalidated LLM output.

4. Verify each step:
   - Run unit tests frequently (`python -m pytest`).
   - Ensure regression tests remain 100% green.
   - Inspect modified files to avoid unintended edits or style regressions.

5. Prepare for completion:
   - Once all code and tests are verified, follow `PROMPT/03_End_Chat.md` to finalize documentation and handoff.
