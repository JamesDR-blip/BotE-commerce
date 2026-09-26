# API Reference

The API is implemented with FastAPI and exposes an OpenAPI 3.1 document.

## Interactive documentation

When the API is running:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI document: `/openapi.json`

The generated OpenAPI contract is the authoritative API reference for request and response schemas.

The current repository audit verifies:

- OpenAPI version: `3.1.0`
- Paths: `60`
- Operations: `61`
- Schemas: `71`
- Schema references: `145`
- Missing schema references: `0`
- Operations without responses: `0`

Every operation has:

- a summary;
- a description;
- a tag.

## Endpoint groups

| Tag | Scope |
|---|---|
| System | Service health, readiness, metrics, categories |
| Health | Health metrics and dataset diagnostics |
| Studio | Workspace and project operations |
| Datasets | Dataset creation, upload, retrieval and listing |
| Data | Upload, cleaning, extraction, mapping and validation |
| Workflows | Workflow definitions, versions, simulation and execution |
| Executions | Execution history, detail and reports |
| Approval | Approval requests and decisions |
| ChangeSets | ChangeSet inspection and rollback |
| Risk | Risk evaluation |
| Lineage | Dataset lineage and audit information |
| Channels | Channel listing and synchronization |
| Rules | Rule search and recommendation |
| Copilot | Copilot sessions, chat and workflow authoring |
| marketplace | Marketplace package listing and installation |

## Compatibility

`api/schemas.py` remains a backward-compatible re-export layer for the response schemas.

Execution report endpoints are retained as compatibility APIs.

## API verification

The repository validates the generated OpenAPI document by constructing the application and checking:

1. OpenAPI version is `3.1.0`.
2. Every operation has a response definition.
3. Every referenced component schema exists.
4. Every operation has summary, description and tags.

The generated document should be inspected rather than manually duplicated when exact request or response models are required.
