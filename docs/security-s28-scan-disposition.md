# S28 Dependency Scan Disposition

## ChromaDB server advisories

The S28 `pip-audit` report identifies these ChromaDB advisories:

- `PYSEC-2026-311` / `CVE-2026-45829`
- `PYSEC-2026-3814` / `CVE-2026-45833`
- `PYSEC-2026-3815` / `CVE-2026-45831`
- `PYSEC-2026-3813` / `CVE-2026-45830`

The advisory descriptions in the captured scan concern ChromaDB's separately
hosted server API. This application constructs only `chromadb.PersistentClient`
for local embedded storage. It does not configure an HTTP Chroma client or run a
Chroma server. The regression test
`test_chroma_retriever_does_not_expose_remote_server_configuration` guards this
deployment boundary.

CI retains and uploads the unfiltered `pip-audit` report, then ignores only the
four listed ChromaDB advisory IDs for the blocking audit step because their
described server attack surface is not enabled here. This is a scoped
non-applicability disposition, not a claim that the installed ChromaDB release
has no advisories. Reassess it before enabling or exposing a Chroma server and
when a fixed upstream release becomes available.

## pip advisory

The captured scan also reported `PYSEC-2026-3721` for pip 26.1.2, with a fixed
version listed by the advisory. CI now explicitly installs pip 26.2 or newer
before project dependencies and scanning.
