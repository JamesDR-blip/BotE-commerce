\# ENGINEERING RULES



\## General



1\. Inspect existing code before creating new abstractions.

2\. Reuse existing services/capabilities where possible.

3\. Avoid duplicate business logic.

4\. Keep changes small and reversible.

5\. Do not introduce breaking changes without justification.



\## Domain



\- No framework dependencies.

\- No database imports.

\- No HTTP imports.

\- No LLM provider imports.



\## Application



\- Business use cases live here.

\- Coordinates domain services and repositories.



\## Agents



Agents may reason and propose.



Agents may NOT:

\- directly modify database

\- bypass risk engine

\- bypass approval policy

\- execute arbitrary code

\- execute arbitrary SQL



\## LLM



LLM output must be validated.



Use Pydantic/domain contracts.



\## Testing



Every new behavior requires tests.



Regression tests must remain green.



\## Security



Never use:

eval()

exec()

unsafe deserialization

unsafe YAML

arbitrary SQL

unvalidated tool calls

