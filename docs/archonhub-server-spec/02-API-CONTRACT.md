# 02-API-CONTRACT

_Generated from the current ArchonHub source tree on 2026-07-03._

## Overview

- Mounted router groups under `/api`: **34**.
- HTTP route decorators inside those routers: **214**.
- Additional transport surfaces outside the router set: `GET /` and `WEBSOCKET /ws`.
- Default auth mechanism is bearer JWT via `Authorization: Bearer <token>`; some routes also accept a matching `X-API-Token` through `get_current_user()`.
- The actual code currently exposes several public utility/OAuth endpoints in addition to login/register/root, so this document follows source truth rather than older security notes.

## Public routes present in the current code

- `GET /`
- `GET /api/alpaca/status`
- `GET /api/capitol-trades/status`
- `GET /api/connectors/oauth/gmail/callback`
- `GET /api/connectors/oauth/gmail/init`
- `GET /api/connectors/oauth/google/callback`
- `GET /api/connectors/oauth/microsoft/callback`
- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/register`
- `WEBSOCKET /ws (auth message required after accept)`

## Group index

| Group | Endpoints |
| --- | ---: |
| Hub entrypoints | 2 |
| Authentication | 4 |
| Runs and queue | 6 |
| Todos | 5 |
| Notifications | 5 |
| Trips | 5 |
| Connectors and OAuth | 12 |
| Projects and clients | 10 |
| Conversations | 4 |
| DevOps | 1 |
| Agents | 8 |
| Automations | 9 |
| Scheduler | 4 |
| Skills | 3 |
| Memory | 8 |
| GOAP planning | 1 |
| Inez orchestration | 7 |
| Briefing and briefs | 6 |
| Search, events, and context | 3 |
| Prompt templates | 5 |
| Knowledge, documents, and integrations | 14 |
| Files | 7 |
| Feedback and corrections | 5 |
| Email cleanup | 6 |
| Reports | 5 |
| Models | 4 |
| Sandbox | 2 |
| Intelligence | 4 |
| Users | 5 |
| Config, stats, health, and briefing | 6 |
| Providers and import | 3 |
| Plans | 15 |
| Alpaca brokerage | 15 |
| Capitol Trades | 14 |
| Web search | 3 |

## Hub entrypoints

The application root redirects the browser to the static dashboard, while `/ws` provides the authenticated realtime event channel used by runs, Inez, and notification fan-out.

**Endpoint count:** 2

### GET `/`

- **Handler:** `root`
- **Auth:** Public
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** 302 redirect to `/web` for the single-file dashboard.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\hub_server.py:171`.

### WEBSOCKET `/ws`

- **Handler:** `websocket_endpoint`
- **Auth:** WebSocket auth message
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** After auth, emits `{type:"connected", queue_depth, active_runs}` and then streams run/notification events.
- **Errors:** 1008 close on timeout, malformed first message, or failed auth
- **Notes:** First message must arrive within 15 seconds and be `{type:"auth", token}` or `{type:"auth", api_token}`. After authentication, only `ping` is consumed inbound; all business traffic is server-emitted.


## Authentication

Identity bootstrap and account maintenance: login, guarded registration, current-user introspection, and password rotation.

**Endpoint count:** 4

### POST `/api/auth/login`

- **Handler:** `login`
- **Auth:** Public
- **Request:** JSON body: `LoginRequest` = `username`:str, `password`:str. Query/form params: `request` (Request).
- **Response:** Returns `{access_token, token_type:"bearer", user}`.
- **Errors:** 400 validation or bad input; 401 invalid credentials; 429 after 10 attempts in 5 minutes from the same IP
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\auth_routes.py:27`.

### POST `/api/auth/register`

- **Handler:** `register`
- **Auth:** Public
- **Request:** JSON body `RegisterRequest`; after bootstrap the caller must already authenticate as admin via bearer JWT or matching `X-API-Token`.
- **Response:** Returns the created user object; first-user bootstrap is auto-promoted to admin.
- **Errors:** 400 validation or bad input; 400 username already exists; 403 admin required after bootstrap
- **Notes:** Unlike older generated docs, the current code returns only the new user object, not a token wrapper.

### GET `/api/auth/me`

- **Handler:** `me`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns the current public user record.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\auth_routes.py:59`.

### POST `/api/auth/change-password`

- **Handler:** `change_password`
- **Auth:** Authenticated
- **Request:** JSON body `ChangePasswordRequest` with `current_password` and `new_password`.
- **Response:** Returns `{ok: true}` on success.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 400 new password too short; 401 current password mismatch
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\auth_routes.py:69`.


## Runs and queue

Run submission, run history, cancellation, and queue pause/resume are the operational front door for background graph execution.

**Endpoint count:** 6

### POST `/api/runs`

- **Handler:** `create_run`
- **Auth:** Authenticated
- **Request:** JSON body: `RunRequest` = `agent_id`:str, `project`:str, `graph`:str (default 'reflexion'), `task`:str, `max_revisions`:int (default 2), `priority`:str (default 'normal').
- **Response:** Creates or queues `runs`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:15`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.

### GET `/api/runs`

- **Handler:** `list_runs`
- **Auth:** Authenticated
- **Request:** Query/form params: `limit` (int, default Query(50, ge=1, le=500)), `agent_id` (Optional[str], default Query(default=None)), `project` (Optional[str], default Query(default=None)), `status_filter` (Optional[str], default Query(default=None, alias='status')).
- **Response:** Returns a list, summary, or inspection payload for `runs`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:22`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.

### POST `/api/runs/{run_id}/cancel`

- **Handler:** `cancel_run`
- **Auth:** Authenticated
- **Request:** Path params: `run_id` (str).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:34`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.

### GET `/api/queue`

- **Handler:** `get_queue`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `queue`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:44`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.

### POST `/api/queue/pause`

- **Handler:** `pause_queue`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:51`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.

### POST `/api/queue/resume`

- **Handler:** `resume_queue`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\runs.py:58`. Primary storage touchpoints: `job_queue`, `runs`, `ws_events`.


## Todos

Simple CRUD surface over the shared `todos` table used by Inez, agents, and dashboard clients.

**Endpoint count:** 5

### GET `/api/todos`

- **Handler:** `get_todos`
- **Auth:** Authenticated
- **Request:** Query/form params: `status_filter` (Optional[str], default Query(default=None, alias='status')), `project` (Optional[str], default Query(default=None)).
- **Response:** Returns a list, summary, or inspection payload for `todos`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\todos.py:16`. Primary storage touchpoints: `todos`.

### POST `/api/todos`

- **Handler:** `create_todo`
- **Auth:** Authenticated
- **Request:** JSON body: `TodoCreate` = `title`:str, `description`:str (default ''), `priority`:str (default 'medium'), `status`:str (default 'pending'), `project`:str (default ''), `due_date`:str (default ''), `tags`:List[Any] (default []), `source`:str (default 'user').
- **Response:** Creates or queues `todos`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\todos.py:33`. Primary storage touchpoints: `todos`.

### GET `/api/todos/{id}`

- **Handler:** `get_todo`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `todos`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\todos.py:57`. Primary storage touchpoints: `todos`.

### PUT `/api/todos/{id}`

- **Handler:** `update_todo`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `TodoUpdate` = `title`:Optional[str] (default None), `description`:Optional[str] (default None), `priority`:Optional[str] (default None), `status`:Optional[str] (default None), `project`:Optional[str] (default None), `due_date`:Optional[str] (default None), `tags`:Optional[List[Any]] (default None).
- **Response:** Returns the updated `todos` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\todos.py:66`. Primary storage touchpoints: `todos`.

### DELETE `/api/todos/{id}`

- **Handler:** `delete_todo`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `todos` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\todos.py:78`. Primary storage touchpoints: `todos`.


## Notifications

In-app notification listing plus acknowledgement/clearing operations backed by `notifications` and websocket broadcasts.

**Endpoint count:** 5

### GET `/api/notifications`

- **Handler:** `list_notifications`
- **Auth:** Authenticated
- **Request:** Query/form params: `unread_only` (bool, default Query(False)).
- **Response:** Returns a list, summary, or inspection payload for `notifications`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\notifications.py:25`. Primary storage touchpoints: `notifications`.

### POST `/api/notifications/read`

- **Handler:** `mark_notifications_read`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Creates or queues `read`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\notifications.py:35`. Primary storage touchpoints: `notifications`.

### DELETE `/api/notifications`

- **Handler:** `clear_notifications`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a deletion acknowledgement for the targeted `notifications` resource.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\notifications.py:47`. Primary storage touchpoints: `notifications`.

### GET `/api/monitoring/notifications`

- **Handler:** `get_monitoring_notifications`
- **Auth:** Authenticated
- **Request:** Query/form params: `viewed` (Optional[bool], default None), `limit` (int, default 50).
- **Response:** Returns a list, summary, or inspection payload for `notifications`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\notifications.py:58`. Primary storage touchpoints: `notifications`.

### POST `/api/monitoring/notifications/{notification_id}/dismiss`

- **Handler:** `dismiss_monitoring_notification`
- **Auth:** Authenticated
- **Request:** Path params: `notification_id` (str).
- **Response:** Creates or queues `dismiss`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\notifications.py:104`. Primary storage touchpoints: `notifications`.


## Trips

Travel trip CRUD stored in `travel_trips`, including budget/spend fields used by travel agents.

**Endpoint count:** 5

### GET `/api/trips`

- **Handler:** `list_trips`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `trips`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\trips.py:14`. Primary storage touchpoints: `travel_trips`.

### POST `/api/trips`

- **Handler:** `create_trip`
- **Auth:** Authenticated
- **Request:** JSON body: `TripCreate` = `name`:str, `destination`:str, `depart_date`:str (default ''), `return_date`:str (default ''), `status`:str (default 'planning'), `budget`:float (default 0.0), `notes`:str (default '').
- **Response:** Creates or queues `trips`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\trips.py:20`. Primary storage touchpoints: `travel_trips`.

### GET `/api/trips/{id}`

- **Handler:** `get_trip`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `trips`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\trips.py:41`. Primary storage touchpoints: `travel_trips`.

### PUT `/api/trips/{id}`

- **Handler:** `update_trip`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `TripUpdate` = `name`:Optional[str] (default None), `destination`:Optional[str] (default None), `depart_date`:Optional[str] (default None), `return_date`:Optional[str] (default None), `status`:Optional[str] (default None), `budget`:Optional[float] (default None), `spent`:Optional[float] (default None), `notes`:Optional[str] (default None).
- **Response:** Returns the updated `trips` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\trips.py:50`. Primary storage touchpoints: `travel_trips`.

### DELETE `/api/trips/{id}`

- **Handler:** `delete_trip`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `trips` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\trips.py:61`. Primary storage touchpoints: `travel_trips`.


## Connectors and OAuth

Email connector CRUD plus Google/Gmail/Microsoft OAuth bootstrap and callback flows stored in `email_connectors`.

**Endpoint count:** 12

### GET `/api/connectors`

- **Handler:** `list_connectors`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `connectors`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:33`. Primary storage touchpoints: `email_connectors`.

### POST `/api/connectors`

- **Handler:** `create_connector`
- **Auth:** Authenticated
- **Request:** JSON body: `ConnectorCreate` = `label`:str, `email_address`:str, `provider`:str (default 'imap'), `auth_type`:str (default 'password'), `imap_host`:str (default ''), `imap_port`:int (default 993), `smtp_host`:str (default ''), `smtp_port`:int (default 587), `username`:str (default ''), `credentials`:dict (default {}), `oauth_client_id`:str (default ''), `oauth_client_secret`:str (default '').
- **Response:** Creates or queues `connectors`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:38`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/{id}`

- **Handler:** `get_connector`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `connectors`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:65`. Primary storage touchpoints: `email_connectors`.

### PUT `/api/connectors/{id}`

- **Handler:** `update_connector`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `ConnectorUpdate` = `label`:Optional[str] (default None), `email_address`:Optional[str] (default None), `imap_host`:Optional[str] (default None), `imap_port`:Optional[int] (default None), `smtp_host`:Optional[str] (default None), `smtp_port`:Optional[int] (default None), `username`:Optional[str] (default None), `credentials`:Optional[dict] (default None), `oauth_client_id`:Optional[str] (default None), `oauth_client_secret`:Optional[str] (default None), `status`:Optional[str] (default None).
- **Response:** Returns the updated `connectors` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:73`. Primary storage touchpoints: `email_connectors`.

### DELETE `/api/connectors/{id}`

- **Handler:** `delete_connector`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `connectors` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:83`. Primary storage touchpoints: `email_connectors`.

### POST `/api/connectors/{id}/test`

- **Handler:** `test_connector_endpoint`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Creates or queues `test`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:90`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/google/init`

- **Handler:** `google_oauth_init`
- **Auth:** Authenticated
- **Request:** Other inputs: body value `connector_id` (str).
- **Response:** Returns a list, summary, or inspection payload for `init`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:113`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/google/callback`

- **Handler:** `google_oauth_callback`
- **Auth:** Public
- **Request:** OAuth callback query parameters `code` and `state`; no JSON body.
- **Response:** Returns a list, summary, or inspection payload for `callback`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:132`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/gmail/init`

- **Handler:** `gmail_oauth_init`
- **Auth:** Public
- **Request:** Other inputs: body value `connector_id` (str).
- **Response:** Returns a list, summary, or inspection payload for `init`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** This wrapper delegates to Google init without its own dependency guard, so it is effectively public even though the underlying Google init endpoint requires auth. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/gmail/callback`

- **Handler:** `gmail_oauth_callback`
- **Auth:** Public
- **Request:** OAuth callback query parameters `code` and `state`; no JSON body.
- **Response:** Returns a list, summary, or inspection payload for `callback`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:182`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/microsoft/init`

- **Handler:** `microsoft_oauth_init`
- **Auth:** Authenticated
- **Request:** Other inputs: body value `connector_id` (str).
- **Response:** Returns a list, summary, or inspection payload for `init`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:187`. Primary storage touchpoints: `email_connectors`.

### GET `/api/connectors/oauth/microsoft/callback`

- **Handler:** `microsoft_oauth_callback`
- **Auth:** Public
- **Request:** OAuth callback query parameters `code` and `state`; no JSON body.
- **Response:** Returns a list, summary, or inspection payload for `callback`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\connectors.py:206`. Primary storage touchpoints: `email_connectors`.


## Projects and clients

Project portfolio CRUD and client CRM CRUD exposed from one router over `projects` and `clients`.

**Endpoint count:** 10

### GET `/api/projects`

- **Handler:** `list_projects`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `projects`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:14`. Primary storage touchpoints: `projects`, `clients`.

### POST `/api/projects`

- **Handler:** `create_project`
- **Auth:** Authenticated
- **Request:** JSON body: `ProjectCreate` = `slug`:str, `name`:str, `description`:str (default ''), `status`:str (default 'active'), `lead_agent`:str (default ''), `tags`:List[Any] (default []).
- **Response:** Creates or queues `projects`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:20`. Primary storage touchpoints: `projects`, `clients`.

### GET `/api/projects/{id}`

- **Handler:** `get_project`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `projects`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:40`. Primary storage touchpoints: `projects`, `clients`.

### PUT `/api/projects/{id}`

- **Handler:** `update_project`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `ProjectUpdate` = `name`:Optional[str] (default None), `description`:Optional[str] (default None), `status`:Optional[str] (default None), `lead_agent`:Optional[str] (default None), `tags`:Optional[List[Any]] (default None).
- **Response:** Returns the updated `projects` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:49`. Primary storage touchpoints: `projects`, `clients`.

### DELETE `/api/projects/{id}`

- **Handler:** `delete_project`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `projects` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:60`. Primary storage touchpoints: `projects`, `clients`.

### GET `/api/clients`

- **Handler:** `list_clients`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `clients`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:68`. Primary storage touchpoints: `projects`, `clients`.

### POST `/api/clients`

- **Handler:** `create_client`
- **Auth:** Authenticated
- **Request:** JSON body: `ClientCreate` = `slug`:str, `name`:str, `business_type`:str (default ''), `service`:str (default ''), `contact_name`:str (default ''), `contact_email`:str (default ''), `engagement`:str (default 'retainer'), `status`:str (default 'active'), `project_slug`:str (default ''), `notes`:str (default '').
- **Response:** Creates or queues `clients`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:74`. Primary storage touchpoints: `projects`, `clients`.

### GET `/api/clients/{id}`

- **Handler:** `get_client`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `clients`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:97`. Primary storage touchpoints: `projects`, `clients`.

### PUT `/api/clients/{id}`

- **Handler:** `update_client`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `ClientUpdate` = `name`:Optional[str] (default None), `business_type`:Optional[str] (default None), `service`:Optional[str] (default None), `contact_name`:Optional[str] (default None), `contact_email`:Optional[str] (default None), `engagement`:Optional[str] (default None), `status`:Optional[str] (default None), `project_slug`:Optional[str] (default None), `notes`:Optional[str] (default None).
- **Response:** Returns the updated `clients` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:106`. Primary storage touchpoints: `projects`, `clients`.

### DELETE `/api/clients/{id}`

- **Handler:** `delete_client`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `clients` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\projects.py:117`. Primary storage touchpoints: `projects`, `clients`.


## Conversations

Conversation threads and message append/list flows backed by `conversations` and `messages`.

**Endpoint count:** 4

### GET `/api/conversations`

- **Handler:** `list_conversations`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `conversations`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\conversations.py:14`. Primary storage touchpoints: `conversations`, `messages`.

### POST `/api/conversations`

- **Handler:** `create_conversation`
- **Auth:** Authenticated
- **Request:** JSON body: `ConversationCreate` = `title`:str, `slug`:str (default 'global').
- **Response:** Creates or queues `conversations`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\conversations.py:20`. Primary storage touchpoints: `conversations`, `messages`.

### GET `/api/conversations/{id}/messages`

- **Handler:** `list_messages`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a list, summary, or inspection payload for `messages`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\conversations.py:35`. Primary storage touchpoints: `conversations`, `messages`.

### POST `/api/conversations/{id}/messages`

- **Handler:** `create_message`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `MessageCreate` = `role`:str, `content`:str, `agent_id`:str (default '').
- **Response:** Creates or queues `messages`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\conversations.py:43`. Primary storage touchpoints: `conversations`, `messages`.


## DevOps

Operational utility surface for local maintenance and developer support.

**Endpoint count:** 1

### GET `/api/devops/status`

- **Handler:** `devops_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns live status/availability data for `status`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\devops.py:52`.


## Agents

Agent registry CRUD, capability lookup, stored agent-to-agent conversation history, and collaboration helpers.

**Endpoint count:** 8

### GET `/api/agents`

- **Handler:** `list_agents_endpoint`
- **Auth:** Authenticated
- **Request:** Query/form params: `project_slug` (Optional[str], default None), `type` (Optional[str], default None), `status` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `agents`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:27`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### POST `/api/agents`

- **Handler:** `upsert_agent_endpoint`
- **Auth:** Authenticated
- **Request:** JSON body: `AgentUpsert` = `agent_id`:str, `name`:str, `type`:str (default 'specialist'), `role`:str (default ''), `description`:str (default ''), `project_slug`:str (default ''), `capabilities`:List[str] (default []), `integrations`:List[str] (default []), `status`:str (default 'active'), `system_prompt`:str (default ''), `config`:dict (default {}), `metadata`:dict (default {}).
- **Response:** Creates or queues `agents`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:45`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### GET `/api/agents/capabilities`

- **Handler:** `get_agent_capabilities`
- **Auth:** Authenticated
- **Request:** Query/form params: `agent_name` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `capabilities`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:93`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### GET `/api/agents/conversations`

- **Handler:** `list_agent_conversations`
- **Auth:** Authenticated
- **Request:** Query/form params: `status` (Optional[str], default None), `limit` (int, default 50).
- **Response:** Returns a list, summary, or inspection payload for `conversations`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:106`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### GET `/api/agents/conversations/{conversation_id}`

- **Handler:** `get_conversation_history`
- **Auth:** Authenticated
- **Request:** Path params: `conversation_id` (str).
- **Response:** Returns one `conversations`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:146`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### GET `/api/agents/{agent_id}`

- **Handler:** `get_agent_endpoint`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str).
- **Response:** Returns one `agents`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:159`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### PUT `/api/agents/{agent_id}`

- **Handler:** `update_agent_endpoint`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str). JSON body: `AgentUpdate` = `name`:Optional[str] (default None), `type`:Optional[str] (default None), `role`:Optional[str] (default None), `description`:Optional[str] (default None), `project_slug`:Optional[str] (default None), `capabilities`:Optional[List[str]] (default None), `integrations`:Optional[List[str]] (default None), `status`:Optional[str] (default None), `system_prompt`:Optional[str] (default None), `config`:Optional[dict] (default None), `metadata`:Optional[dict] (default None).
- **Response:** Returns the updated `agents` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:169`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.

### POST `/api/agents/collaborate`

- **Handler:** `agent_collaboration`
- **Auth:** Authenticated
- **Request:** Query/form params: `request` (dict).
- **Response:** Creates or queues `collaborate`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\agents.py:193`. Primary storage touchpoints: `agent_registry`, `agent_capabilities`, `agent_conversations`.


## Automations

Automation definition CRUD plus runs/documents inspection and manual trigger endpoints.

**Endpoint count:** 9

### GET `/api/automations`

- **Handler:** `list_automations`
- **Auth:** Authenticated
- **Request:** Query/form params: `project_slug` (Optional[str], default None), `status` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `automations`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:17`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### POST `/api/automations`

- **Handler:** `create_automation`
- **Auth:** Authenticated
- **Request:** JSON body: `AutomationCreate` = `slug`:str, `name`:str, `description`:str (default ''), `project_slug`:str (default ''), `agent_id`:str (default ''), `trigger_type`:str (default 'manual'), `trigger_config`:dict (default {}), `steps`:List[Any] (default []), `status`:str (default 'active').
- **Response:** Creates or queues `automations`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:32`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### GET `/api/automations/{id}`

- **Handler:** `get_automation`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `automations`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:46`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### PUT `/api/automations/{id}`

- **Handler:** `update_automation`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `AutomationUpdate` = `name`:Optional[str] (default None), `description`:Optional[str] (default None), `project_slug`:Optional[str] (default None), `agent_id`:Optional[str] (default None), `trigger_type`:Optional[str] (default None), `trigger_config`:Optional[dict] (default None), `steps`:Optional[List[Any]] (default None), `status`:Optional[str] (default None).
- **Response:** Returns the updated `automations` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:54`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### DELETE `/api/automations/{id}`

- **Handler:** `delete_automation`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `automations` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:64`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### POST `/api/automations/{id}/trigger`

- **Handler:** `trigger_automation`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:71`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### GET `/api/automations/{id}/runs`

- **Handler:** `list_automation_runs`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `runs`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:88`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### GET `/api/automations/{id}/documents`

- **Handler:** `list_automation_docs`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `documents`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:94`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.

### POST `/api/automations/{id}/documents`

- **Handler:** `create_automation_doc`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `AutomationDocCreate` = `automation_id`:str (default ''), `run_id`:str (default ''), `title`:str (default ''), `doc_type`:str (default 'report'), `content`:str (default ''), `status`:str (default 'draft'), `reviewed_by`:str (default ''), `review_notes`:str (default '').
- **Response:** Creates or queues `documents`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\automations.py:100`. Primary storage touchpoints: `automations`, `automation_runs`, `automation_documents`.


## Scheduler

User-defined scheduled jobs stored in `scheduled_jobs`, plus immediate execution and deletion.

**Endpoint count:** 4

### GET `/api/scheduler`

- **Handler:** `list_scheduler`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `scheduler`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\scheduler.py:61`. Primary storage touchpoints: `scheduled_jobs`.

### POST `/api/scheduler`

- **Handler:** `create_scheduler_job`
- **Auth:** Authenticated
- **Request:** JSON body: `SchedulerJobCreate` = `agent_id`:str, `project`:str, `graph`:str (default 'reflexion'), `task`:str, `run_type`:str (default 'cron'), `cron_expr`:str (default ''), `interval_sec`:int (default 0).
- **Response:** Creates or queues `scheduler`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\scheduler.py:76`. Primary storage touchpoints: `scheduled_jobs`.

### DELETE `/api/scheduler/{id}`

- **Handler:** `delete_scheduler_job`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `scheduler` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\scheduler.py:135`. Primary storage touchpoints: `scheduled_jobs`.

### POST `/api/scheduler/{id}/trigger`

- **Handler:** `trigger_scheduler_job`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\scheduler.py:149`. Primary storage touchpoints: `scheduled_jobs`.


## Skills

Agent skill retrieval and mutation over the `skills`/skill-file layer.

**Endpoint count:** 3

### GET `/api/skills`

- **Handler:** `list_skills`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `skills`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\skills.py:12`. Primary storage touchpoints: `skills`, `agent_skill_levels`.

### GET `/api/skills/{agent_id}`

- **Handler:** `get_skill`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str).
- **Response:** Returns one `skills`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\skills.py:25`. Primary storage touchpoints: `skills`, `agent_skill_levels`.

### PUT `/api/skills/{agent_id}`

- **Handler:** `update_skill`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str). Query/form params: `body` (dict).
- **Response:** Returns the updated `skills` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\skills.py:31`. Primary storage touchpoints: `skills`, `agent_skill_levels`.


## Memory

Per-agent and global memory read/write endpoints backed by `agent_memory` and `global_memory`.

**Endpoint count:** 8

### GET `/api/memory/agents/{agent_id}`

- **Handler:** `get_memory`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str).
- **Response:** Returns one `agents`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:17`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### PUT `/api/memory/agents/{agent_id}`

- **Handler:** `update_memory`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str). JSON body: `MemoryUpdate` = `data`:dict.
- **Response:** Returns the updated `agents` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:22`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### GET `/api/memory/global`

- **Handler:** `list_global_memory`
- **Auth:** Authenticated
- **Request:** Query/form params: `category` (Optional[str], default None), `limit` (int, default 100), `offset` (int, default 0).
- **Response:** Returns a list, summary, or inspection payload for `global`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:29`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### GET `/api/memory/global/search`

- **Handler:** `search_global_memory`
- **Auth:** Authenticated
- **Request:** Other inputs: body value `q` (str).
- **Response:** Returns a list, summary, or inspection payload for `search`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:45`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### POST `/api/memory/global`

- **Handler:** `create_global_memory_fact`
- **Auth:** Authenticated
- **Request:** JSON body: `MemoryFactBody` = `category`:str, `key`:str, `value`:str, `importance`:int (default 5), `source`:str (default 'user'), `confidence`:float (default 1.0).
- **Response:** Creates or queues `global`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:55`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### PUT `/api/memory/global/{fact_id}`

- **Handler:** `update_global_memory_fact`
- **Auth:** Authenticated
- **Request:** Path params: `fact_id` (str). JSON body: `MemoryFactBody` = `category`:str, `key`:str, `value`:str, `importance`:int (default 5), `source`:str (default 'user'), `confidence`:float (default 1.0).
- **Response:** Returns the updated `global` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:76`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### DELETE `/api/memory/global/{fact_id}`

- **Handler:** `delete_global_memory_fact`
- **Auth:** Authenticated
- **Request:** Path params: `fact_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `global` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:98`. Primary storage touchpoints: `agent_memory`, `global_memory`.

### POST `/api/memory/global/extract`

- **Handler:** `extract_memory_from_conversation`
- **Auth:** Authenticated
- **Request:** Query/form params: `body` (dict).
- **Response:** Creates or queues `extract`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\memory.py:108`. Primary storage touchpoints: `agent_memory`, `global_memory`.


## GOAP planning

A single GOAP planning endpoint that can also write generated plans into the plan inbox for later execution.

**Endpoint count:** 1

### POST `/api/goap/plan`

- **Handler:** `create_plan`
- **Auth:** Authenticated
- **Request:** JSON body `PlanRequest` with `goal`, `project`, and optional `write_to_inbox`.
- **Response:** Returns a `PlanResponse` object with `plan_id`, `steps`, `complexity`, and optional `inbox_path`.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\goap.py:30`.


## Inez orchestration

Interactive chief-of-staff chat, morning brief/status surfaces, memory inspection, and durable run-event replay.

**Endpoint count:** 7

### POST `/api/inez/chat`

- **Handler:** `inez_chat`
- **Auth:** Authenticated
- **Request:** JSON body `InezChatRequest` (`message`, optional `conversation_id`).
- **Response:** Creates or queues `chat`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** The router persists a durable `run_events` stream in parallel with websocket emits so reconnecting clients can replay missed events. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### GET `/api/inez/runs/{run_id}/events`

- **Handler:** `inez_run_events`
- **Auth:** Authenticated
- **Request:** Path params: `run_id` (str). Query/form params: `after` (int, default 0).
- **Response:** Returns a list, summary, or inspection payload for `events`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:194`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### GET `/api/inez/conversations/{conversation_id}/events`

- **Handler:** `inez_conversation_events`
- **Auth:** Authenticated
- **Request:** Path params: `conversation_id` (str). Query/form params: `after` (int, default 0).
- **Response:** Returns durable event-log rows scoped to a conversation after the supplied cursor.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:208`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### GET `/api/inez/brief`

- **Handler:** `inez_morning_brief`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `brief`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:219`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### GET `/api/inez/status`

- **Handler:** `inez_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns live status/availability data for `status`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:229`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### GET `/api/inez/memory`

- **Handler:** `inez_memory`
- **Auth:** Authenticated
- **Request:** Query/form params: `conversation_id` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `memory`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:239`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.

### DELETE `/api/inez/memory/facts/{key}`

- **Handler:** `delete_inez_fact`
- **Auth:** Authenticated
- **Request:** Path params: `key` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `facts` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\inez.py:261`. Primary storage touchpoints: `run_events`, `agent_memory`, `todos`.


## Briefing and briefs

Two related surfaces: durable user-created briefs plus cached/generated morning briefing endpoints.

**Endpoint count:** 6

### GET `/api/briefs`

- **Handler:** `list_briefs`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `briefs`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:25`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.

### POST `/api/briefs`

- **Handler:** `create_brief`
- **Auth:** Authenticated
- **Request:** Query/form params: `body` (dict).
- **Response:** Creates or queues `briefs`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:34`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.

### DELETE `/api/briefs/{id}`

- **Handler:** `delete_brief`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `briefs` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:46`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.

### GET `/api/briefing/morning`

- **Handler:** `get_morning_briefing`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** GET returns the cached/generated morning brief; POST forces regeneration.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:75`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.

### POST `/api/briefing/morning`

- **Handler:** `generate_morning_briefing`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** GET returns the cached/generated morning brief; POST forces regeneration.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:81`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.

### GET `/api/briefing/history`

- **Handler:** `get_briefing_history`
- **Auth:** Authenticated
- **Request:** Query/form params: `limit` (int, default 30).
- **Response:** Returns a list, summary, or inspection payload for `history`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\briefing.py:138`. Primary storage touchpoints: `daily_briefs`, `morning_briefs`.


## Search, events, and context

FTS-backed message search, events inspection, and context expansion for dashboards and chat surfaces.

**Endpoint count:** 3

### GET `/api/search`

- **Handler:** `search_conversations`
- **Auth:** Authenticated
- **Request:** Query/form params: `q` (str, default Query(..., description='Search query')), `limit` (int, default Query(20, ge=1, le=100, description='Max results')).
- **Response:** Returns FTS conversation/message matches.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\search.py:13`. Primary storage touchpoints: `messages_fts`, `messages`, `events_log`.

### GET `/api/events`

- **Handler:** `list_events`
- **Auth:** Authenticated
- **Request:** Query/form params: `event_type` (Optional[str], default None), `level` (Optional[str], default None), `limit` (int, default 100).
- **Response:** Returns a list, summary, or inspection payload for `events`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\search.py:100`. Primary storage touchpoints: `messages_fts`, `messages`, `events_log`.

### GET `/api/context`

- **Handler:** `get_full_context`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `context`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\search.py:119`. Primary storage touchpoints: `messages_fts`, `messages`, `events_log`.


## Prompt templates

Reusable prompt-template CRUD plus a “use” endpoint that records or expands a selected template.

**Endpoint count:** 5

### GET `/api/prompt-templates`

- **Handler:** `list_prompt_templates`
- **Auth:** Authenticated
- **Request:** Query/form params: `category` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `prompt-templates`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\prompt_templates.py:14`. Primary storage touchpoints: `prompt_templates`.

### POST `/api/prompt-templates`

- **Handler:** `create_prompt_template`
- **Auth:** Authenticated
- **Request:** Query/form params: `body` (dict).
- **Response:** Creates or queues `prompt-templates`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\prompt_templates.py:54`. Primary storage touchpoints: `prompt_templates`.

### PUT `/api/prompt-templates/{template_id}`

- **Handler:** `update_prompt_template`
- **Auth:** Authenticated
- **Request:** Path params: `template_id` (str). Query/form params: `body` (dict).
- **Response:** Returns the updated `prompt-templates` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\prompt_templates.py:104`. Primary storage touchpoints: `prompt_templates`.

### DELETE `/api/prompt-templates/{template_id}`

- **Handler:** `delete_prompt_template`
- **Auth:** Authenticated
- **Request:** Path params: `template_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `prompt-templates` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\prompt_templates.py:167`. Primary storage touchpoints: `prompt_templates`.

### POST `/api/prompt-templates/{template_id}/use`

- **Handler:** `use_prompt_template`
- **Auth:** Authenticated
- **Request:** Path params: `template_id` (str).
- **Response:** Creates or queues `use`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\prompt_templates.py:194`. Primary storage touchpoints: `prompt_templates`.


## Knowledge, documents, and integrations

Knowledge base CRUD, document CRUD, and integration registry endpoints for long-lived context.

**Endpoint count:** 14

### GET `/api/knowledge`

- **Handler:** `list_knowledge`
- **Auth:** Authenticated
- **Request:** Query/form params: `category` (Optional[str], default None), `project_slug` (Optional[str], default None), `q` (Optional[str], default None), `limit` (int, default 50).
- **Response:** Returns a list, summary, or inspection payload for `knowledge`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:19`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### POST `/api/knowledge`

- **Handler:** `create_knowledge`
- **Auth:** Authenticated
- **Request:** JSON body: `KnowledgeCreate` = `title`:str, `content`:str, `source`:str (default ''), `source_type`:str (default 'manual'), `category`:str (default 'general'), `tags`:List[str] (default []), `project_slug`:str (default ''), `agent_id`:str (default '').
- **Response:** Creates or queues `knowledge`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:53`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### GET `/api/knowledge/{id}`

- **Handler:** `get_knowledge`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `knowledge`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:66`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### PUT `/api/knowledge/{id}`

- **Handler:** `update_knowledge`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `KnowledgeUpdate` = `title`:Optional[str] (default None), `content`:Optional[str] (default None), `category`:Optional[str] (default None), `tags`:Optional[List[str]] (default None), `project_slug`:Optional[str] (default None), `is_active`:Optional[bool] (default None).
- **Response:** Returns the updated `knowledge` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:74`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### DELETE `/api/knowledge/{id}`

- **Handler:** `delete_knowledge`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `knowledge` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:86`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### GET `/api/documents`

- **Handler:** `list_documents`
- **Auth:** Authenticated
- **Request:** Query/form params: `project_slug` (Optional[str], default None), `doc_type` (Optional[str], default None), `client_id` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `documents`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:98`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### POST `/api/documents`

- **Handler:** `create_document`
- **Auth:** Authenticated
- **Request:** JSON body: `DocumentCreate` = `title`:str, `doc_type`:str (default 'general'), `content`:str (default ''), `format`:str (default 'markdown'), `project_slug`:str (default ''), `client_id`:str (default ''), `tags`:List[str] (default []), `created_by`:str (default '').
- **Response:** Creates or queues `documents`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:116`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### GET `/api/documents/{id}`

- **Handler:** `get_document`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns one `documents`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:130`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### PUT `/api/documents/{id}`

- **Handler:** `update_document`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str). JSON body: `DocumentUpdate` = `title`:Optional[str] (default None), `content`:Optional[str] (default None), `doc_type`:Optional[str] (default None), `status`:Optional[str] (default None), `tags`:Optional[List[str]] (default None).
- **Response:** Returns the updated `documents` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:138`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### DELETE `/api/documents/{id}`

- **Handler:** `delete_document_ep`
- **Auth:** Authenticated
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `documents` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:148`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### GET `/api/integrations`

- **Handler:** `list_integrations`
- **Auth:** Authenticated
- **Request:** Query/form params: `provider` (Optional[str], default None), `entity_type` (Optional[str], default None).
- **Response:** Returns a list, summary, or inspection payload for `integrations`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:160`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### POST `/api/integrations`

- **Handler:** `upsert_integration`
- **Auth:** Authenticated
- **Request:** JSON body: `IntegrationUpsert` = `name`:str, `provider`:str, `entity_type`:str (default 'global'), `entity_id`:str (default ''), `auth_type`:str (default 'oauth2'), `credentials`:dict (default {}), `scope`:str (default ''), `status`:str (default 'pending'), `metadata`:dict (default {}).
- **Response:** Creates or queues `integrations`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:180`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### GET `/api/integrations/{id}`

- **Handler:** `get_integration`
- **Auth:** Admin
- **Request:** Path params: `id` (str).
- **Response:** Returns one `integrations`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:193`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.

### DELETE `/api/integrations/{id}`

- **Handler:** `delete_integration`
- **Auth:** Admin
- **Request:** Path params: `id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `integrations` resource.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\knowledge.py:201`. Primary storage touchpoints: `knowledge_base`, `documents`, `integrations`.


## Files

Upload, list, fetch, delete, embed, and semantic search over `uploaded_files`/`file_chunks`.

**Endpoint count:** 7

### POST `/api/files/upload`

- **Handler:** `upload_file`
- **Auth:** Authenticated
- **Request:** Query/form params: `file` (bytes, default None), `filename` (str, default None), `mime_type` (str, default None), `conversation_id` (Optional[str], default None), `message_id` (Optional[str], default None).
- **Response:** Creates or queues `upload`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:23`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### GET `/api/files/{file_id}`

- **Handler:** `get_file`
- **Auth:** Authenticated
- **Request:** Path params: `file_id` (str).
- **Response:** Returns one `files`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:70`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### GET `/api/files`

- **Handler:** `list_files`
- **Auth:** Authenticated
- **Request:** Query/form params: `limit` (int, default 50).
- **Response:** Returns a list, summary, or inspection payload for `files`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:93`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### POST `/api/files/{file_id}/embed`

- **Handler:** `embed_file`
- **Auth:** Authenticated
- **Request:** Path params: `file_id` (str).
- **Response:** Creates or queues `embed`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:114`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### GET `/api/files/_search`

- **Handler:** `search_documents`
- **Auth:** Authenticated
- **Request:** Query/form params: `limit` (int, default 5), `file_ids` (Optional[str], default None). Other inputs: body value `query` (str).
- **Response:** Returns semantic/keyword file-search matches across uploaded content.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:137`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### POST `/api/files/upload/form`

- **Handler:** `upload_file_form`
- **Auth:** Authenticated
- **Request:** Other inputs: multipart upload file payload.
- **Response:** Creates or queues `form`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:163`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.

### DELETE `/api/files/{file_id}`

- **Handler:** `delete_file`
- **Auth:** Authenticated
- **Request:** Path params: `file_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `files` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\files.py:198`. Primary storage touchpoints: `uploaded_files`, `file_chunks`.


## Feedback and corrections

Message ratings, corrections, preference analysis, and feedback statistics feeding the learning layer.

**Endpoint count:** 5

### POST `/api/messages/{message_id}/feedback`

- **Handler:** `submit_feedback`
- **Auth:** Authenticated
- **Request:** Path params: `message_id` (str). Query/form params: `request` (dict).
- **Response:** Creates or queues `feedback`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\feedback.py:24`. Primary storage touchpoints: `message_feedback`, `corrections`, `user_style_preferences`.

### POST `/api/corrections`

- **Handler:** `submit_correction`
- **Auth:** Authenticated
- **Request:** Query/form params: `request` (dict).
- **Response:** Creates or queues `corrections`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\feedback.py:80`. Primary storage touchpoints: `message_feedback`, `corrections`, `user_style_preferences`.

### GET `/api/feedback/stats`

- **Handler:** `get_feedback_stats`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `stats`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\feedback.py:137`. Primary storage touchpoints: `message_feedback`, `corrections`, `user_style_preferences`.

### GET `/api/feedback/analyze`

- **Handler:** `analyze_feedback`
- **Auth:** Authenticated
- **Request:** Query/form params: `days` (int, default 7).
- **Response:** Returns a list, summary, or inspection payload for `analyze`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\feedback.py:188`. Primary storage touchpoints: `message_feedback`, `corrections`, `user_style_preferences`.

### GET `/api/feedback/preferences`

- **Handler:** `get_user_preferences`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `preferences`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\feedback.py:206`. Primary storage touchpoints: `message_feedback`, `corrections`, `user_style_preferences`.


## Email cleanup

Inbox analysis, plan review, and cleanup execution endpoints over `email_cleanup_plans` and `email_cleanup_items`.

**Endpoint count:** 6

### POST `/api/email/cleanup/analyze`

- **Handler:** `analyze_email_cleanup`
- **Auth:** Authenticated
- **Request:** Query/form params: `request` (dict).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:22`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.

### GET `/api/email/cleanup/plans`

- **Handler:** `list_cleanup_plans`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `plans`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:47`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.

### GET `/api/email/cleanup/plans/{plan_id}`

- **Handler:** `get_cleanup_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Returns one `plans`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:70`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.

### PUT `/api/email/cleanup/plans/{plan_id}/approve`

- **Handler:** `approve_cleanup_items`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). Query/form params: `request` (dict).
- **Response:** Returns the updated `approve` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:89`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.

### POST `/api/email/cleanup/plans/{plan_id}/execute`

- **Handler:** `execute_cleanup_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). Query/form params: `background_tasks` (BackgroundTasks).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:121`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.

### GET `/api/email/cleanup/history`

- **Handler:** `get_cleanup_history`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `history`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\email_cleanup.py:142`. Primary storage touchpoints: `email_cleanup_plans`, `email_cleanup_items`.


## Reports

Report catalog inspection plus admin-triggered report runs and deletion.

**Endpoint count:** 5

### GET `/api/reports`

- **Handler:** `list_reports_endpoint`
- **Auth:** Authenticated
- **Request:** Query/form params: `report_type` (Optional[str], default None), `project_slug` (Optional[str], default None), `job_id` (Optional[str], default None), `limit` (int, default 100).
- **Response:** Returns a list, summary, or inspection payload for `reports`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\reports.py:28`. Primary storage touchpoints: `reports`.

### GET `/api/reports/types/summary`

- **Handler:** `report_types_summary`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `summary`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\reports.py:41`. Primary storage touchpoints: `reports`.

### GET `/api/reports/{report_id}`

- **Handler:** `get_report_endpoint`
- **Auth:** Authenticated
- **Request:** Path params: `report_id` (str).
- **Response:** Returns one `reports`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\reports.py:50`. Primary storage touchpoints: `reports`.

### DELETE `/api/reports/{report_id}`

- **Handler:** `delete_report_endpoint`
- **Auth:** Admin
- **Request:** Path params: `report_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `reports` resource.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\reports.py:60`. Primary storage touchpoints: `reports`.

### POST `/api/reports/run`

- **Handler:** `run_report_endpoint`
- **Auth:** Admin
- **Request:** JSON body `ReportRunRequest` selecting the report job and optional extra context.
- **Response:** Creates or queues `run`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input
- **Notes:** Admin-triggered report execution is separate from APScheduler; it can be invoked on demand. Primary storage touchpoints: `reports`.


## Models

Model catalog listing, enable/disable controls, task routing, and provider catalog inspection.

**Endpoint count:** 4

### GET `/api/models`

- **Handler:** `list_models`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `models`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\models_api.py:22`.

### PUT `/api/models/toggle`

- **Handler:** `toggle_model`
- **Auth:** Admin
- **Request:** JSON body `ModelToggle` (`provider`, `model_id`, `enabled`).
- **Response:** Returns the updated `toggle` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\models_api.py:30`.

### POST `/api/models/route`

- **Handler:** `route_model`
- **Auth:** Authenticated
- **Request:** JSON body `ModelRouteRequest` (`task_type`, optional `agent_id`).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\models_api.py:39`.

### GET `/api/models/providers`

- **Handler:** `list_providers`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `providers`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\models_api.py:53`.


## Sandbox

Ephemeral code execution surface for contained experiments and diagnostics.

**Endpoint count:** 2

### GET `/api/sandbox/status`

- **Handler:** `sandbox_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns live status/availability data for `status`.
- **Errors:** 401 missing or invalid auth; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\sandbox.py:14`.

### POST `/api/sandbox/execute`

- **Handler:** `sandbox_execute`
- **Auth:** Authenticated
- **Request:** JSON body `SandboxExecuteRequest` (`code`, `language`, optional `data_files`).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\sandbox.py:23`.


## Intelligence

Aggregated intelligence and portfolio insight endpoints produced from the knowledge, run, and planning data sets.

**Endpoint count:** 4

### GET `/api/intelligence/summary`

- **Handler:** `intelligence_summary`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `summary`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\intelligence.py:11`.

### GET `/api/intelligence/skills`

- **Handler:** `intelligence_skills`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `skills`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\intelligence.py:21`.

### GET `/api/intelligence/patterns`

- **Handler:** `intelligence_patterns`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `patterns`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\intelligence.py:32`.

### GET `/api/intelligence/agent/{agent_id}`

- **Handler:** `intelligence_agent`
- **Auth:** Authenticated
- **Request:** Path params: `agent_id` (str).
- **Response:** Returns one `agent`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\intelligence.py:42`.


## Users

Admin-only user administration over the `users` table.

**Endpoint count:** 5

### GET `/api/users`

- **Handler:** `list_users`
- **Auth:** Admin
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `users`.
- **Errors:** 401 missing or invalid auth; 403 admin role required
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\users.py:12`. Primary storage touchpoints: `users`.

### POST `/api/users`

- **Handler:** `create_user_endpoint`
- **Auth:** Admin
- **Request:** JSON body: `RegisterRequest` = `username`:str, `email`:str, `password`:str, `role`:str (default 'user').
- **Response:** Creates or queues `users`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\users.py:23`. Primary storage touchpoints: `users`.

### GET `/api/users/{id}`

- **Handler:** `get_user`
- **Auth:** Admin
- **Request:** Path params: `id` (int).
- **Response:** Returns one `users`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\users.py:31`. Primary storage touchpoints: `users`.

### PUT `/api/users/{id}`

- **Handler:** `update_user`
- **Auth:** Admin
- **Request:** Path params: `id` (int). JSON body: `UserUpdate` = `email`:Optional[str] (default None), `role`:Optional[str] (default None), `is_active`:Optional[bool] (default None).
- **Response:** Returns the updated `users` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\users.py:40`. Primary storage touchpoints: `users`.

### DELETE `/api/users/{id}`

- **Handler:** `delete_user`
- **Auth:** Admin
- **Request:** Path params: `id` (int).
- **Response:** Returns a deletion acknowledgement for the targeted `users` resource.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\users.py:52`. Primary storage touchpoints: `users`.


## Config, stats, health, and briefing

Public health plus authenticated stats/briefing and admin-only config management.

**Endpoint count:** 6

### GET `/api/health`

- **Handler:** `health`
- **Auth:** Public
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns process health/availability status for unauthenticated probes.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:26`. Primary storage touchpoints: `hub_config`.

### GET `/api/config`

- **Handler:** `get_config`
- **Auth:** Admin
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `config`.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:68`. Primary storage touchpoints: `hub_config`.

### PUT `/api/config`

- **Handler:** `update_config`
- **Auth:** Admin
- **Request:** JSON body: `ConfigUpdate` = `data`:dict.
- **Response:** Returns the updated `config` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:81`. Primary storage touchpoints: `hub_config`.

### GET `/api/stats`

- **Handler:** `get_stats`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `stats`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:95`. Primary storage touchpoints: `hub_config`.

### GET `/api/briefing`

- **Handler:** `get_briefing`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `briefing`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:101`. Primary storage touchpoints: `hub_config`.

### POST `/api/monitoring/run`

- **Handler:** `run_monitoring`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Creates or queues `run`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\config_api.py:106`. Primary storage touchpoints: `hub_config`.


## Providers and import

Provider import/configuration endpoints used to synchronize external provider definitions.

**Endpoint count:** 3

### POST `/api/import`

- **Handler:** `run_data_import`
- **Auth:** Admin
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Creates or queues `import`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 403 admin role required; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\providers.py:11`. Primary storage touchpoints: `integrations`.

### POST `/api/providers/sync-free-keys`

- **Handler:** `sync_free_llm_keys_endpoint`
- **Auth:** Authenticated
- **Request:** Query/form params: `body` (dict, default None).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\providers.py:27`. Primary storage touchpoints: `integrations`.

### GET `/api/providers/free-keys-status`

- **Handler:** `free_keys_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `free-keys-status`.
- **Errors:** 401 missing or invalid auth
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\providers.py:44`. Primary storage touchpoints: `integrations`.


## Plans

Plan inbox scanning, plan CRUD, drift proposals/review, node responses, and plan execution orchestration.

**Endpoint count:** 15

### POST `/api/plans/scan`

- **Handler:** `scan_plan_inbox`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 500 planner/executor/provider failure
- **Notes:** Imports `.yaml`, `.yml`, and `.json` plans from the plan inbox folder. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### GET `/api/plans/inbox/status`

- **Handler:** `plan_inbox_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns live status/availability data for `status`.
- **Errors:** 401 missing or invalid auth; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:163`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans`

- **Handler:** `create_plan`
- **Auth:** Authenticated
- **Request:** POST accepts `CreatePlanBody` describing nodes, edges, constraints, tags, and optional `entry_node`.
- **Response:** Creates or queues `plans`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:311`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### GET `/api/plans`

- **Handler:** `list_plans`
- **Auth:** Authenticated
- **Request:** POST accepts `CreatePlanBody` describing nodes, edges, constraints, tags, and optional `entry_node`.
- **Response:** Returns a list, summary, or inspection payload for `plans`.
- **Errors:** 401 missing or invalid auth; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:388`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### GET `/api/plans/{plan_id}`

- **Handler:** `get_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Returns one `plans`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:398`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### PATCH `/api/plans/{plan_id}`

- **Handler:** `patch_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). JSON body: `PatchPlanBody` = `title`:Optional[str] (default None), `objective`:Optional[str] (default None), `status`:Optional[str] (default None), `tags`:Optional[list[str]] (default None).
- **Response:** Returns the updated `plans` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:406`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/preflight`

- **Handler:** `preflight_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Creates or queues `preflight`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:423`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/approve`

- **Handler:** `approve_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:463`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/execute`

- **Handler:** `execute_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:483`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/abandon`

- **Handler:** `abandon_plan`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). Query/form params: `reason` (str, default Query('')).
- **Response:** Creates or queues `abandon`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:515`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/propose-drift`

- **Handler:** `propose_drift`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). JSON body: `ProposeDriftBody` = `drift_notes`:str, `new_nodes`:list[NodeBody] (default []), `new_edges`:list[EdgeBody] (default []).
- **Response:** Creates or queues `propose-drift`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:532`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/drift/approve`

- **Handler:** `approve_drift`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:601`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/drift/reject`

- **Handler:** `reject_drift`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). JSON body: `DriftReviewBody` = `rejection_reason`:str (default '').
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:641`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### GET `/api/plans/{plan_id}/events`

- **Handler:** `get_events`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str). Query/form params: `limit` (int, default Query(200, ge=1, le=500)).
- **Response:** Returns a list, summary, or inspection payload for `events`.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:672`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.

### POST `/api/plans/{plan_id}/nodes/{node_id}/respond`

- **Handler:** `respond_to_node`
- **Auth:** Authenticated
- **Request:** Path params: `plan_id` (str), `node_id` (str). JSON body: `NodeRespondBody` = `decision`:str, `notes`:str (default '').
- **Response:** Creates or queues `respond`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\plans.py:680`. Primary storage touchpoints: `implementation_plans`, `plan_node_events`.


## Alpaca brokerage

Brokerage status/account/positions/orders/market-data endpoints, with order writes mirrored into `alpaca_orders`.

**Endpoint count:** 15

### GET `/api/alpaca/status`

- **Handler:** `alpaca_status`
- **Auth:** Public
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns `{configured, paper, alpaca_ok}`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:72`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/account`

- **Handler:** `alpaca_account`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `account`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:77`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/positions`

- **Handler:** `alpaca_positions`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `positions`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:86`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/positions/{symbol}`

- **Handler:** `alpaca_position`
- **Auth:** Authenticated
- **Request:** Path params: `symbol` (str).
- **Response:** Returns one `positions`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:95`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/orders`

- **Handler:** `alpaca_orders`
- **Auth:** Authenticated
- **Request:** GET accepts query parameters (`status`, `limit`, optional comma-separated `symbols`); POST accepts `PlaceOrderRequest`.
- **Response:** Returns a list, summary, or inspection payload for `orders`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** POST also mirrors the broker response into `alpaca_orders` with `submitted_by`, `agent_reason`, and raw broker JSON. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### POST `/api/alpaca/orders`

- **Handler:** `alpaca_place_order`
- **Auth:** Authenticated
- **Request:** GET accepts query parameters (`status`, `limit`, optional comma-separated `symbols`); POST accepts `PlaceOrderRequest`.
- **Response:** Creates or queues `orders`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** POST also mirrors the broker response into `alpaca_orders` with `submitted_by`, `agent_reason`, and raw broker JSON. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### DELETE `/api/alpaca/orders/{order_id}`

- **Handler:** `alpaca_cancel_order`
- **Auth:** Authenticated
- **Request:** Path params: `order_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `orders` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:170`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### DELETE `/api/alpaca/orders`

- **Handler:** `alpaca_cancel_all_orders`
- **Auth:** Authenticated
- **Request:** GET accepts query parameters (`status`, `limit`, optional comma-separated `symbols`); POST accepts `PlaceOrderRequest`.
- **Response:** Returns a deletion acknowledgement for the targeted `orders` resource.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** POST also mirrors the broker response into `alpaca_orders` with `submitted_by`, `agent_reason`, and raw broker JSON. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/portfolio/history`

- **Handler:** `alpaca_portfolio_history`
- **Auth:** Authenticated
- **Request:** Query parameters `period` and `timeframe`.
- **Response:** Returns a list, summary, or inspection payload for `history`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:196`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/assets/{symbol}`

- **Handler:** `alpaca_asset`
- **Auth:** Authenticated
- **Request:** Path params: `symbol` (str).
- **Response:** Returns one `assets`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:209`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/quotes/{symbol}`

- **Handler:** `alpaca_quote`
- **Auth:** Authenticated
- **Request:** Path params: `symbol` (str).
- **Response:** Returns one `quotes`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:218`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/bars/{symbol}`

- **Handler:** `alpaca_bars`
- **Auth:** Authenticated
- **Request:** Path `symbol`; query `timeframe`, `limit`, `start`, `end`.
- **Response:** Returns one `bars`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:227`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/clock`

- **Handler:** `alpaca_clock`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `clock`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:243`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### GET `/api/alpaca/calendar`

- **Handler:** `alpaca_calendar`
- **Auth:** Authenticated
- **Request:** Optional `start` and `end` query parameters.
- **Response:** Returns a list, summary, or inspection payload for `calendar`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:252`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.

### POST `/api/alpaca/sync-positions`

- **Handler:** `alpaca_sync_positions`
- **Auth:** Authenticated
- **Request:** JSON body: `SyncPositionsRequest` = `overwrite`:bool (default True).
- **Response:** Returns the computed result payload and any server-side side effects summary.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\alpaca.py:265`. Primary storage touchpoints: `alpaca_orders`, `market_positions`.


## Capitol Trades

Tracked politician CRUD, disclosure ingestion, signal generation, CRO review, and downstream Alpaca execution.

**Endpoint count:** 14

### GET `/api/capitol-trades/status`

- **Handler:** `capitol_trades_status`
- **Auth:** Public
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns live status/availability data for `status`.
- **Errors:** FastAPI default `detail` error payloads on unexpected failures.
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:350`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/politicians`

- **Handler:** `list_politicians`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `politicians`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:358`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### POST `/api/capitol-trades/politicians`

- **Handler:** `add_politician`
- **Auth:** Authenticated
- **Request:** JSON body: `AddPoliticianRequest` = `name`:str, `chamber`:str (default 'both'), `tracking_reason`:str, `party`:str (default ''), `state`:str (default '').
- **Response:** Creates or queues `politicians`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:370`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/politicians/{politician_id}`

- **Handler:** `get_politician`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str).
- **Response:** Returns one `politicians`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:411`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### PATCH `/api/capitol-trades/politicians/{politician_id}`

- **Handler:** `update_politician`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str). JSON body: `UpdatePoliticianRequest` = `tracking_reason`:Optional[str] (default None), `performance_note`:Optional[str] (default None), `is_active`:Optional[bool] (default None).
- **Response:** Returns the updated `politicians` record or an acknowledgement of the patch.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:422`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### DELETE `/api/capitol-trades/politicians/{politician_id}`

- **Handler:** `delete_politician`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str).
- **Response:** Returns a deletion acknowledgement for the targeted `politicians` resource.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:455`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/politicians/{politician_id}/trades`

- **Handler:** `get_politician_trades`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str).
- **Response:** Returns one `trades`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:469`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/politicians/{politician_id}/signals`

- **Handler:** `get_politician_signals`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str).
- **Response:** Returns one `signals`-scoped record or detail payload.
- **Errors:** 401 missing or invalid auth; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:484`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### POST `/api/capitol-trades/politicians/{politician_id}/refresh`

- **Handler:** `refresh_politician`
- **Auth:** Authenticated
- **Request:** Path params: `politician_id` (str).
- **Response:** Creates or queues `refresh`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:505`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/trades`

- **Handler:** `list_trades`
- **Auth:** Authenticated
- **Request:** Query/form params: `ticker` (Optional[str], default Query(None)), `politician_id` (Optional[str], default Query(None)), `days` (int, default Query(30, ge=1, le=3650)), `limit` (int, default Query(100, ge=1, le=500)).
- **Response:** Returns a list, summary, or inspection payload for `trades`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:518`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/signals`

- **Handler:** `list_signals`
- **Auth:** Authenticated
- **Request:** Query/form params: `status` (Optional[str], default Query('pending')), `limit` (int, default Query(50, ge=1, le=500)).
- **Response:** Returns a list, summary, or inspection payload for `signals`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:546`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### POST `/api/capitol-trades/signals/{signal_id}/review`

- **Handler:** `review_signal`
- **Auth:** Authenticated
- **Request:** Path params: `signal_id` (str). JSON body: `ReviewSignalRequest` = `action`:str, `cro_notes`:str (default ''), `qty`:Optional[float] (default None), `time_in_force`:str (default 'day'), `order_type`:str (default 'market'), `limit_price`:Optional[float] (default None).
- **Response:** Returns an acknowledgement/status payload describing the requested action.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 404 missing resource where applicable; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:576`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### POST `/api/capitol-trades/refresh-all`

- **Handler:** `refresh_all_politicians`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Creates or queues `refresh-all`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:679`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.

### GET `/api/capitol-trades/leaderboard`

- **Handler:** `copy_trading_leaderboard`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns a list, summary, or inspection payload for `leaderboard`.
- **Errors:** 401 missing or invalid auth; 422 missing broker credentials/config; 503 optional trading dependency unavailable
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\capitol_trades.py:699`. Primary storage touchpoints: `tracked_politicians`, `politician_trades`, `copy_trade_signals`, `alpaca_orders`.


## Web search

SerpAPI-backed web search GET/POST plus configuration status checks used by Inez and dashboards.

**Endpoint count:** 3

### GET `/api/search/web`

- **Handler:** `web_search`
- **Auth:** Authenticated
- **Request:** Query/form params: `q` (str, default Query(..., description='Search query')), `limit` (int, default Query(5, ge=1, le=20)).
- **Response:** Returns a list, summary, or inspection payload for `web`.
- **Errors:** 401 missing or invalid auth; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\web_search_api.py:19`.

### POST `/api/search/web`

- **Handler:** `web_search_post`
- **Auth:** Authenticated
- **Request:** Query/form params: `body` (dict).
- **Response:** Creates or queues `web`-related work and returns the created/acknowledgement payload.
- **Errors:** 401 missing or invalid auth; 400 validation or bad input; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\web_search_api.py:45`.

### GET `/api/search/web/status`

- **Handler:** `web_search_status`
- **Auth:** Authenticated
- **Request:** No JSON body; only the route path and optional auth headers are required.
- **Response:** Returns search-provider configuration status.
- **Errors:** 401 missing or invalid auth; 500 planner/executor/provider failure
- **Notes:** Implemented in `.agents\agentharness\app\v3\routers\web_search_api.py:70`.
