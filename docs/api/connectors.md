# Connectors and OAuth API
_Generated from the current ArchonHub source tree on 2026-06-24 03:23 UTC._
## Overview
Connectors unify IMAP/SMTP credentials, OAuth token storage, and higher-level integrations such as Gmail or Microsoft 365 email access.
## Authentication and Response Rules
- Authenticated endpoints use `Authorization: Bearer <jwt>`.
- Standard success envelope for feature endpoints is `{"success": true, ...}` unless the handler returns a bare object such as `/api/auth/me` or `/api/runs`.
- Error payloads are returned as `{"detail": "error message"}` with the relevant HTTP status.
- Timestamps should be treated as ISO 8601 UTC strings; older rows may omit trailing `Z` because the local engine uses naive UTC serialization in a few places.
## Endpoint Index
| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | /api/connectors | list_connectors | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| POST | /api/connectors | create_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| PUT | /api/connectors/{id} | update_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| DELETE | /api/connectors/{id} | delete_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| POST | /api/connectors/{id}/test | test_connector_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/google/init | google_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/google/callback | google_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/gmail/init | gmail_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/gmail/callback | gmail_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/microsoft/init | microsoft_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/microsoft/callback | microsoft_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/integrations | list_integrations | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/integrations | upsert_integration | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/integrations/{id} | get_integration | Admin JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/integrations/{id} | delete_integration | Admin JWT | .agents/agentharness/app/v3/routers/knowledge.py |
## Detailed Endpoints
### GET `/api/connectors`
- **Handler:** `list_connectors`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Lists connector rows.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/connectors`
- **Handler:** `create_connector`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| label | str | required |
| email_address | str | required |
| provider | str | "imap" |
| auth_type | str | "password" |
| imap_host | str | "" |
| imap_port | int | 993 |
| smtp_host | str | "" |
| smtp_port | int | 587 |
| username | str | "" |
| credentials | dict | Field(default_factory=dict) |
| oauth_client_id | str | "" |
| oauth_client_secret | str | "" |
#### Response Schema
- Creates a connector row.
#### Example
```bash
curl -X POST http://localhost:8765/api/connectors \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"label": "string", "email_address": "string", "provider": "string", "auth_type": "string", "imap_host": "string", "imap_port": 1, "smtp_host": "string", "smtp_port": 1, "username": "admin", "credentials": {}, "oauth_client_id": "string", "oauth_client_secret": "string"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### PUT `/api/connectors/{id}`
- **Handler:** `update_connector`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| label | Optional[str] | None |
| email_address | Optional[str] | None |
| imap_host | Optional[str] | None |
| imap_port | Optional[int] | None |
| smtp_host | Optional[str] | None |
| smtp_port | Optional[int] | None |
| username | Optional[str] | None |
| credentials | Optional[dict] | None |
| oauth_client_id | Optional[str] | None |
| oauth_client_secret | Optional[str] | None |
| status | Optional[str] | None |
#### Response Schema
- Updates connector configuration.
#### Example
```bash
curl -X PUT http://localhost:8765/api/connectors/{id} \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"label": "string", "email_address": "string", "imap_host": "string", "imap_port": 1, "smtp_host": "string", "smtp_port": 1, "username": "admin", "credentials": "value", "oauth_client_id": "string", "oauth_client_secret": "string", "status": "string"}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### DELETE `/api/connectors/{id}`
- **Handler:** `delete_connector`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Deletes a connector.
#### Example
```bash
curl -X DELETE http://localhost:8765/api/connectors/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### POST `/api/connectors/{id}/test`
- **Handler:** `test_connector_endpoint`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Tests a connector configuration.
#### Example
```bash
curl -X POST http://localhost:8765/api/connectors/{id}/test \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/google/init`
- **Handler:** `google_oauth_init`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Starts the Google OAuth flow.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/google/init \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/google/callback`
- **Handler:** `google_oauth_callback`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Handles the Google OAuth callback.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/google/callback \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/gmail/init`
- **Handler:** `gmail_oauth_init`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Alias/init surface for Gmail OAuth.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/gmail/init \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/gmail/callback`
- **Handler:** `gmail_oauth_callback`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Alias/callback surface for Gmail OAuth.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/gmail/callback \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/microsoft/init`
- **Handler:** `microsoft_oauth_init`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Starts the Microsoft 365 OAuth flow.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/microsoft/init \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/connectors/oauth/microsoft/callback`
- **Handler:** `microsoft_oauth_callback`
- **Auth required:** No JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/connectors.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Handles the Microsoft 365 OAuth callback.
#### Example
```bash
curl -X GET http://localhost:8765/api/connectors/oauth/microsoft/callback \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/integrations`
- **Handler:** `list_integrations`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Lists generic integration records.
#### Example
```bash
curl -X GET http://localhost:8765/api/integrations \
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
### POST `/api/integrations`
- **Handler:** `upsert_integration`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
| Field | Type | Default / Rule |
| --- | --- | --- |
| name | str | required |
| provider | str | required |
| entity_type | str | "global" |
| entity_id | str | "" |
| auth_type | str | "oauth2" |
| credentials | dict | Field(default_factory=dict) |
| scope | str | "" |
| status | str | "pending" |
| metadata | dict | Field(default_factory=dict) |
#### Response Schema
- Creates a generic integration record.
#### Example
```bash
curl -X POST http://localhost:8765/api/integrations \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <jwt>' \
  -d '{"name": "string", "provider": "string", "entity_type": "string", "entity_id": "string", "auth_type": "string", "credentials": {}, "scope": "string", "status": "string", "metadata": {}}'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### GET `/api/integrations/{id}`
- **Handler:** `get_integration`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Returns one integration.
#### Example
```bash
curl -X GET http://localhost:8765/api/integrations/{id} \
  -H 'Authorization: Bearer <jwt>'
```
```json
{
  "success": true,
  "data": "see endpoint-specific payload"
}
```
### DELETE `/api/integrations/{id}`
- **Handler:** `delete_integration`
- **Auth required:** Bearer JWT required.
- **Source:** `.agents/agentharness/app/v3/routers/knowledge.py`
#### Request Body
No JSON body; use query/path parameters only.
#### Response Schema
- Deletes one integration.
#### Example
```bash
curl -X DELETE http://localhost:8765/api/integrations/{id} \
  -H 'Authorization: Bearer <jwt>'
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
- [Microsoft 365 integration](../features/m365-integration.md)
- [Email cleanup](email.md)
## Source References

- `.agents/agentharness/app/v3/routers/connectors.py`
- `.agents/agentharness/app/v3/routers/knowledge.py`
