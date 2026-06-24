# Agents, Runs, and Queue API
_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._
## Overview
This surface covers the live agent registry, queued work, and historical runs. It is the core execution API for launching specialists, monitoring queue depth, and administering the local agent roster.
## Authentication and Response Rules
- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.
## Endpoint Index
| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| POST | /api/runs | create_run | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/runs | list_runs | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/runs/{run_id}/cancel | cancel_run | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/queue | get_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/queue/pause | pause_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/queue/resume | resume_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/agents | list_agents_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| POST | /api/agents | upsert_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/{agent_id} | get_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| PUT | /api/agents/{agent_id} | update_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| DELETE | /api/agents/{agent_id} | delete_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/capabilities | get_agent_capabilities | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/conversations/{conversation_id} | get_conversation_history | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| POST | /api/agents/collaborate | agent_collaboration | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
## Detailed Endpoints
### POST `/api/runs`
- **Handler:** `create_run`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| agent_id | str | required |
| project | str | required |
| graph | str | "reflexion" |
| task | str | required |
| max_revisions | int | 2 |
| priority | str | "normal" |
#### Response Schema
- Queues a new run and returns an acknowledgement object with run/job identifiers.
#### Example
```bash
curl -X POST http://localhost:8765/api/runs \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"agent_id": "markets-project-lead", "project": "markets", "graph": "string", "task": "Generate a pre-market brief.", "max_revisions": 1, "priority": "string"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/runs`
- **Handler:** `list_runs`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns recent runs as an array of run objects.
#### Example
```bash
curl -X GET http://localhost:8765/api/runs \
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
### POST `/api/runs/{run_id}/cancel`
- **Handler:** `cancel_run`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Cancels an active run when a cancel flag exists; returns success/failure status.
#### Example
```bash
curl -X POST http://localhost:8765/api/runs/{run_id}/cancel \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/queue`
- **Handler:** `get_queue`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns queue contents and/or queue depth metadata.
#### Example
```bash
curl -X GET http://localhost:8765/api/queue \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/queue/pause`
- **Handler:** `pause_queue`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Pauses the queue worker; admin or authenticated operational caller expected.
#### Example
```bash
curl -X POST http://localhost:8765/api/queue/pause \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/queue/resume`
- **Handler:** `resume_queue`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/runs.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Resumes queue processing.
#### Example
```bash
curl -X POST http://localhost:8765/api/queue/resume \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/agents`
- **Handler:** `list_agents_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns all rows from `agent_registry` with parsed JSON fields.
#### Example
```bash
curl -X GET http://localhost:8765/api/agents \
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
### POST `/api/agents`
- **Handler:** `upsert_agent_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| agent_id | str | required |
| name | str | required |
| type | str | "specialist" |
| role | str | "" |
| description | str | "" |
| project_slug | str | "" |
| capabilities | List[str] | Field(default_factory=list) |
| integrations | List[str] | Field(default_factory=list) |
| status | str | "active" |
| system_prompt | str | "" |
| config | dict | Field(default_factory=dict) |
| metadata | dict | Field(default_factory=dict) |
#### Response Schema
- Creates or upserts an agent registry record.
#### Example
```bash
curl -X POST http://localhost:8765/api/agents \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"agent_id": "markets-project-lead", "name": "string", "type": "string", "role": "string", "description": "string", "project_slug": "string", "capabilities": "value", "integrations": "value", "status": "string", "system_prompt": "string", "config": {}, "metadata": {}}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/agents/{agent_id}`
- **Handler:** `get_agent_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns one agent registry record.
#### Example
```bash
curl -X GET http://localhost:8765/api/agents/{agent_id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### PUT `/api/agents/{agent_id}`
- **Handler:** `update_agent_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| name | Optional[str] | None |
| type | Optional[str] | None |
| role | Optional[str] | None |
| description | Optional[str] | None |
| project_slug | Optional[str] | None |
| capabilities | Optional[List[str]] | None |
| integrations | Optional[List[str]] | None |
| status | Optional[str] | None |
| system_prompt | Optional[str] | None |
| config | Optional[dict] | None |
| metadata | Optional[dict] | None |
#### Response Schema
- Updates mutable agent registry fields, including config and metadata.
#### Example
```bash
curl -X PUT http://localhost:8765/api/agents/{agent_id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"name": "string", "type": "string", "role": "string", "description": "string", "project_slug": "string", "capabilities": "value", "integrations": "value", "status": "string", "system_prompt": "string", "config": "value", "metadata": "value"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### DELETE `/api/agents/{agent_id}`
- **Handler:** `delete_agent_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Deletes the agent registry record.
#### Example
```bash
curl -X DELETE http://localhost:8765/api/agents/{agent_id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/agents/capabilities`
- **Handler:** `get_agent_capabilities`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns capability-oriented agent metadata.
#### Example
```bash
curl -X GET http://localhost:8765/api/agents/capabilities \
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
### GET `/api/agents/conversations/{conversation_id}`
- **Handler:** `get_conversation_history`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns stored agent conversation history for a conversation id.
#### Example
```bash
curl -X GET http://localhost:8765/api/agents/conversations/{conversation_id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/agents/collaborate`
- **Handler:** `agent_collaboration`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/agents.py`
#### Request Body
| Field | Type | Notes |
| --- | --- | --- |
| user_message | string | Required; source text for memory extraction |
| agent_response | string | Optional response text for better extraction context |
#### Response Schema
- Starts a collaboration pattern between multiple agents; exact payload is a generic dict in current code paths.
#### Example
```bash
curl -X POST http://localhost:8765/api/agents/collaborate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"user_message": "Remember that YEPC zoning review is next week.", "agent_response": "Stored."}'
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
- [Agent overview](../agents/overview.md)
- [Dispatch contract](../contracts/dispatch-contract.md)
- [WebSocket](websocket.md)
## Source References

- `.agents/agentharness/app/v3/routers/runs.py`
- `.agents/agentharness/app/v3/routers/agents.py`
- `.agents/agentharness/app/v3/core/hub.py`
