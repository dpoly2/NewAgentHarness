# 07-SECURITY-MODEL

_Generated from the current ArchonHub source tree on 2026-07-03._

## Authentication primitives

- **JWT algorithm:** HS256
- **Token lifetime:** 24 hours (`ACCESS_TOKEN_EXPIRE_HOURS`)
- **Primary dependency:** `get_current_user()`
- **Admin gate:** `get_admin_user()` requires `role == "admin"`
- **Alternate machine auth:** a matching `X-API-Token` is accepted before bearer JWT validation and is elevated to an admin-shaped synthetic user.

## Login protections

`POST /api/auth/login` enforces a simple per-IP in-memory throttle:

- **10 attempts**
- **5-minute window**
- on excess: **HTTP 429**

## Websocket auth contract

`/ws` is accepted first and then expects the first JSON frame within **15 seconds**. The only accepted bootstrap shapes are:

- `{"type":"auth","token":"<jwt>"}`
- `{"type":"auth","api_token":"<api token>"}`

If the client times out, sends malformed JSON, or fails auth, the server closes the socket with code **1008**.

## Startup hardening

The lifespan startup path refuses to boot unless explicitly overridden when either of these are still default:

- `JWT_SECRET`
- `ADMIN_PASSWORD`

That failure can be bypassed only with `ARCHONHUB_UNSAFE_DEFAULTS=1`, which the source treats as a dev-only override.

## Agent-side guardrails

### AgentShield

Both the interactive and specialist execution paths pre-scan prompts:

- `inez_agent.think()` blocks unsafe user messages before tool prefetch or LLM reasoning.
- `agent_runner.run_agent()` blocks unsafe dispatched tasks before skill loading or model routing.

### DB write restrictions

Specialist agents cannot arbitrarily mutate the database. `agent_runner` only applies writes to a small allowlist, and `travel_trips` is further restricted to travel-prefixed agents.

## Current public-surface reality

The standing repo note says nearly all routes should require bearer auth, but the current source still leaves some operational/OAuth endpoints public. In the inspected code, public exceptions include:

- `/`
- `/api/auth/login`
- `/api/auth/register` (bootstrap public; admin-gated once users exist)
- `/api/health`
- `/api/alpaca/status`
- `/api/capitol-trades/status`
- OAuth callback routes under `/api/connectors/oauth/*`
- `GET /api/connectors/oauth/gmail/init`, which delegates to the authenticated Google init helper without adding its own dependency

That mismatch matters for threat modeling and should be treated as code truth until the server implementation changes.

## Error model

- `401`: missing/invalid JWT or bad current password
- `403`: authenticated but not admin where admin routes are used
- `404`: record missing
- `422`: configuration prerequisites absent for broker integrations
- `429`: login throttling
- `500`: uncaught internal failures normalized to `{"detail": "Internal server error"}`

## Source references

- `.agents\agentharness\app\v3\core\auth.py`
- `.agents\agentharness\app\v3\hub_server.py`
- `.agents\agentharness\app\v3\agent_runner.py`
- `.agents\agentharness\app\v3\inez_agent.py`
- `.agents\agentharness\app\v3\routers\connectors.py`
