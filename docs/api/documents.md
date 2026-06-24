# Documents, Knowledge, and Files API
_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._
## Overview
This group covers hand-authored documents, structured knowledge entries, raw file upload/parse/embed flows, and semantic file search.
## Authentication and Response Rules
- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.
## Endpoint Index
| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/documents | list_documents | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/documents | create_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/documents/{id} | get_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| PUT | /api/documents/{id} | update_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/documents/{id} | delete_document_ep | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/knowledge | list_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/knowledge | create_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/knowledge/{id} | get_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| PUT | /api/knowledge/{id} | update_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/knowledge/{id} | delete_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/files/upload | upload_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files/{file_id} | get_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files | list_files | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| POST | /api/files/{file_id}/embed | embed_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files/_search | search_documents | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
## Detailed Endpoints
### GET `/api/documents`
- **Handler:** `list_documents`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Lists documents from the `documents` table.
#### Example
```bash
curl -X GET http://localhost:8765/api/documents \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/documents`
- **Handler:** `create_document`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| title | str | required |
| doc_type | str | "general" |
| content | str | "" |
| format | str | "markdown" |
| project_slug | str | "" |
| client_id | str | "" |
| tags | List[str] | Field(default_factory=list) |
| created_by | str | "" |
#### Response Schema
- Creates a document row.
#### Example
```bash
curl -X POST http://localhost:8765/api/documents \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "doc_type": "string", "content": "string", "format": "string", "project_slug": "string", "client_id": "string", "tags": "value", "created_by": "string"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/documents/{id}`
- **Handler:** `get_document`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns one document.
#### Example
```bash
curl -X GET http://localhost:8765/api/documents/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### PUT `/api/documents/{id}`
- **Handler:** `update_document`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| title | Optional[str] | None |
| content | Optional[str] | None |
| doc_type | Optional[str] | None |
| status | Optional[str] | None |
| tags | Optional[List[str]] | None |
#### Response Schema
- Updates document content or metadata.
#### Example
```bash
curl -X PUT http://localhost:8765/api/documents/{id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "content": "string", "doc_type": "string", "status": "string", "tags": "value"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### DELETE `/api/documents/{id}`
- **Handler:** `delete_document_ep`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Deletes a document row.
#### Example
```bash
curl -X DELETE http://localhost:8765/api/documents/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/knowledge`
- **Handler:** `list_knowledge`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Lists knowledge base entries.
#### Example
```bash
curl -X GET http://localhost:8765/api/knowledge \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/knowledge`
- **Handler:** `create_knowledge`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| title | str | required |
| content | str | required |
| source | str | "" |
| source_type | str | "manual" |
| category | str | "general" |
| tags | List[str] | Field(default_factory=list) |
| project_slug | str | "" |
| agent_id | str | "" |
#### Response Schema
- Creates a knowledge base entry.
#### Example
```bash
curl -X POST http://localhost:8765/api/knowledge \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "content": "string", "source": "string", "source_type": "string", "category": "string", "tags": "value", "project_slug": "string", "agent_id": "markets-project-lead"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/knowledge/{id}`
- **Handler:** `get_knowledge`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns one knowledge entry.
#### Example
```bash
curl -X GET http://localhost:8765/api/knowledge/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### PUT `/api/knowledge/{id}`
- **Handler:** `update_knowledge`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| title | Optional[str] | None |
| content | Optional[str] | None |
| category | Optional[str] | None |
| tags | Optional[List[str]] | None |
| project_slug | Optional[str] | None |
| is_active | Optional[bool] | None |
#### Response Schema
- Updates a knowledge entry.
#### Example
```bash
curl -X PUT http://localhost:8765/api/knowledge/{id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"title": "Example title", "content": "string", "category": "string", "tags": "value", "project_slug": "string", "is_active": true}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### DELETE `/api/knowledge/{id}`
- **Handler:** `delete_knowledge`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Deletes a knowledge entry.
#### Example
```bash
curl -X DELETE http://localhost:8765/api/knowledge/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/files/upload`
- **Handler:** `upload_file`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/files.py`
#### Request Body
| Field | Type | Notes |
| --- | --- | --- |
| file | bytes | Uploaded file contents |
| filename | string | Original filename |
| mime_type | string | Client-provided MIME type |
| user_id | string | Defaults to `default_user` |
| conversation_id | string | Optional conversation link |
| message_id | string | Optional message link |
#### Response Schema
- Saves an uploaded file, parses it, and returns `{ success, file }`.
#### Example
```bash
curl -X POST http://localhost:8765/api/files/upload \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"file": "<bytes>", "filename": "brief.pdf", "mime_type": "application/pdf"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/files/{file_id}`
- **Handler:** `get_file`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/files.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns uploaded file metadata and parsed state.
#### Example
```bash
curl -X GET http://localhost:8765/api/files/{file_id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/files`
- **Handler:** `list_files`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/files.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Lists uploaded files.
#### Example
```bash
curl -X GET http://localhost:8765/api/files \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/files/{file_id}/embed`
- **Handler:** `embed_file`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/files.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Generates embeddings and persists chunk metadata.
#### Example
```bash
curl -X POST http://localhost:8765/api/files/{file_id}/embed \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/files/_search`
- **Handler:** `search_documents`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/files.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Runs semantic search over embedded file chunks.
#### Example
```bash
curl -X GET http://localhost:8765/api/files/_search \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"value": "example"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
## Error Handling
- `400` indicates validation or bad input.
- `401` indicates a missing or invalid JWT.
- `403` indicates the caller is authenticated but lacks the required role, usually admin-only surfaces.
- `404` indicates the resource identifier does not exist.
- `500` indicates an unhandled subsystem error such as missing optional dependencies, database failures, or third-party API failures.
## Client Notes
- The SwiftUI app consumes many of these routes through `HubClient.swift` and `Models.swift`.
- Treat list responses as dynamic; some endpoints return arrays directly instead of a named `items` wrapper.
- Nullable JSON fields appear in several resources and are intentionally modelled as optional in Swift.
## Related Documentation
- [Document RAG feature](../features/document-rag.md)
- [iOS documents view](../ios/views.md)
- [Database schema](../architecture/database-schema.md)
## Source References

- `.agents/agentharness/app/v3/routers/knowledge.py`
- `.agents/agentharness/app/v3/routers/files.py`
