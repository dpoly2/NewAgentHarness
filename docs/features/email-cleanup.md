# Email Cleanup

_Generated on 2026-06-24 03:23 UTC._

## Overview

Email Cleanup is a structured human-in-the-loop workflow: analyze an inbox, generate suggested actions, request approval, execute approved changes, and optionally roll them back within the supported recovery window.

## Architecture

```
connector (IMAP or OAuth2)
  → email_analyzer.fetch_emails_from_connector()
  → categorize_email(...) + plan generation
  → email_cleanup_plans / email_cleanup_items tables
  → approval via API/UI
  → email_executor.execute_cleanup(plan_id)
  → IMAP archive/delete actions
  → plan status + item execution timestamps updated
  → optional rollback_cleanup(plan_id)
```

## Cleanup Flow

1. A connector row identifies the mailbox and auth style.
2. The analyzer fetches recent messages over IMAP and extracts basic metadata, snippets, and unsubscribe signals.
3. Each message is categorized into buckets such as newsletter, promotion, social, spam, old thread, or important.
4. A cleanup plan is written into SQLite with item-level recommended actions.
5. The operator approves or rejects item groups.
6. The executor archives or deletes approved items, updates execution flags, and reports totals/space recovered.
7. A rollback path can attempt to restore items if still inside the 30-day window.

## Categories and heuristics

- `newsletter`: unsubscribe language, known newsletter domains, mailing-list cues.
- `promotion`: sale/discount/deal language.
- `social`: social network notification phrasing.
- `spam`: common spam keywords.
- `old_thread`: age-based heuristic for stale threads.
- `important`: default catch-all when no cleanup rule is strong enough.

## Configuration

- Uses `email_connectors` rows and `oauth_connector.py` token helpers.
- Supports OAuth2 or password-based IMAP auth.
- Gmail and Microsoft 365 have first-class OAuth flows.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `POST /api/email/cleanup/analyze` | Create analysis plan — returns `{plan_id, summary}` only |
| `GET /api/email/cleanup/plans` | List plans |
| `GET /api/email/cleanup/plans/{plan_id}` | Inspect plan — **required** after analyze to get `{plan: {categories: {...}, items: [...]}}` |
| `PUT /api/email/cleanup/plans/{plan_id}/approve` | Approve items (`{item_ids: [...]}`) |
| `POST /api/email/cleanup/plans/{plan_id}/execute` | Execute plan |
| `GET /api/email/cleanup/history` | History |

## Two-Step Analyze Flow

> **Important:** `POST /api/email/cleanup/analyze` returns only `{plan_id, summary}`. The category breakdown and item list are **not** included in the analyze response. Clients must immediately follow with `GET /api/email/cleanup/plans/{plan_id}` to get the full plan with categories and items.

```
POST /api/email/cleanup/analyze → {plan_id, summary}
  ↓
GET /api/email/cleanup/plans/{plan_id} → {plan: {categories: {newsletter: [...], ...}, items: [...]}}
  ↓
PUT /api/email/cleanup/plans/{plan_id}/approve  {item_ids: [...]}
  ↓
POST /api/email/cleanup/plans/{plan_id}/execute
```

## Client Surfaces

| Surface | Feature |
| --- | --- |
| Desktop (Connectors tab → Email Cleanup) | Connector select, Analyze button, category breakdown, item table, approve/execute |
| Webapp (`showEmailCleanup()`) | Connector selector, category cards with counts, item table, approve/execute flow |

## Error Handling

- Missing connector, invalid credentials, or expired tokens abort analysis/execution with an error.
- IMAP fetch failures on individual emails are skipped and logged while the loop continues.
- Cleanup execution records failed IDs so the plan still yields partial results.
- Rollback is refused when more than 30 days have passed since execution.

## Rollback Notes

- Gmail archive/delete semantics differ from generic IMAP folders; the executor contains provider-specific branches.
- Non-Gmail providers may rely on `Archive` existing, and otherwise degrade to flag/deletion behavior.

## Related Documentation

- [Email API](../api/email.md)
- [Connectors API](../api/connectors.md)
- [Microsoft 365 integration](m365-integration.md)

## Source References

- `.agents/agentharness/app/v3/email_analyzer.py`
- `.agents/agentharness/app/v3/email_executor.py`
- `.agents/agentharness/app/v3/oauth_connector.py`

## Implementation Checklist

- Confirm `email cleanup` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `email cleanup` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.
