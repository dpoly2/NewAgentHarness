# ArchonHub — database access contract

**Binding rules for any code that touches the database.** Agents implementing the
Postgres migration (or any feature that reads/writes the DB) MUST follow these.
Reviewers should reject changes that violate them. This exists so the codebase
stays backend-portable and multi-node-safe.

Companion docs: [POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md) (the spec),
[SCALABILITY.md](SCALABILITY.md) (adding nodes).

---

## C1 — Go through the seam, never `import sqlite3` in new code

All DB access goes through the four connection seams: `get_conn()` /
`get_db()` (`hub_db.py`), `_db_connection()` / `_thread_conn()`
(`core/database.py`). New modules MUST NOT `import sqlite3` or open their own
connection. After the adapter lands (`core/db_backend.py`), the seams return the
backend-appropriate connection facade — call sites stay unchanged.

## C2 — Parameterized queries only, `?` placeholders

Use `?` placeholders and pass params as a tuple/list. The adapter translates
`?` → `%s` for Postgres. **Never** f-string or `%`-format a value into SQL
(injection + it breaks the paramstyle translator). Table/column *identifiers*
that must be dynamic go through an allowlist, never string interpolation of user
input.

```python
# yes
conn.execute("SELECT * FROM runs WHERE agent_id = ?", (agent_id,))
# no
conn.execute(f"SELECT * FROM runs WHERE agent_id = '{agent_id}'")
```

## C3 — No SQLite-only idioms

Forbidden in new/migrated code (the adapter does not emulate these):

- `INSERT OR REPLACE` / `INSERT OR IGNORE` → use `INSERT ... ON CONFLICT (<pk>)
  DO UPDATE SET ...` / `DO NOTHING`.
- `cursor.lastrowid` → use `RETURNING id` and read the returned row.
- `PRAGMA ...` → gone. Use `db_backend.table_columns(table)` for introspection.
- `conn.executescript(...)` → execute statements individually (iterate a list).
- `AUTOINCREMENT` in DDL → `BIGINT GENERATED ALWAYS AS IDENTITY`.

## C4 — Respect the connection lifecycle

- Short-lived helpers (most CRUD): open via the seam, use, **close in a
  `finally`** — exactly as the current code does.
- The 4 hot-path pollers (`_insert_ws_event`, `_claim_queued_job`,
  `_check_job_cancel_flag`, `_count_queued_jobs`) use `_thread_conn()` — **do NOT
  close** the returned connection. This contract is unchanged by the migration;
  under Postgres it is a pooled connection pinned to the thread.
- Never share one connection across threads. Never hold a connection open across
  an `await` or a long LLM call.

## C5 — Transactions are explicit and short

- Wrap multi-statement writes in a single transaction; commit once. Do not leave
  a transaction open across network/LLM I/O — it holds locks and blocks other
  nodes.
- Read-modify-write on shared rows (job claiming, counters, leases) MUST be a
  single atomic statement or use `SELECT ... FOR UPDATE [SKIP LOCKED]`. Never
  read in Python, decide, then write back without a row lock — that races across
  workers.

## C6 — Datetimes stay ISO-`TEXT` UTC (for now)

Use `_now_iso()` / `_utcnow()`. Timestamps are naive-UTC ISO strings so
lexicographic comparison equals temporal comparison (the reaper depends on this,
`_reap_stale_jobs`). Do not introduce `timestamptz` columns outside the dedicated
hardening PR (POSTGRES_MIGRATION §9), and if you do, update every comparison site.

## C7 — JSON goes through the JSON helpers

Store structured data with `_json_dumps`, read with `_json_loads`, and declare the
field in the relevant `json_fields` set. Do not hand-roll `json.dumps` at call
sites — keeping it centralized is what lets the JSONB migration happen later
without touching call sites.

## C8 — Multi-node safety by default

Assume **N processes on N machines** run this code simultaneously. Any code path
that "there can only be one of" (scheduler jobs, singleton counters, one-time
migrations) MUST be guarded by the scheduler leader lease
(`_try_acquire_scheduler_lock`) or a DB-level lock. Never assume in-process state
(a module global, a `threading.Lock`) coordinates anything — it only covers one
node. Cross-node coordination lives in the database.

## C9 — Both backends must stay green until cutover

Until production cutover (POSTGRES_MIGRATION M4), every change must pass the test
suite under **both** `DB_BACKEND=sqlite` and `DB_BACKEND=postgres`. Do not add a
feature that only works on one backend. CI runs both.

## C10 — Schema changes are versioned and idempotent

- Bump `_SCHEMA_VERSION` (`core/database.py:874`) when adding a table/column.
- New DDL uses `IF NOT EXISTS` and is safe to run repeatedly (warm-start guard
  skips it, but it must be correct if run).
- Add new built-in scheduler jobs to `_JOB_SPECS` in `hub_scheduler.py` only —
  never call `.scheduler.add_job()` from routers (see project memory).

## C11 — Config and secrets

- Read tunables from `hub_config` (shared, live-reloaded) or env, per existing
  patterns. `JWT_SECRET` and `ADMIN_PASSWORD` MUST be identical across all API
  nodes or tokens issued by one node fail on another.
- `DATABASE_URL` and `DB_BACKEND` come from env, never hardcoded.

---

**Review checklist (paste into PRs that touch the DB):**

- [ ] No new `import sqlite3`; goes through a seam
- [ ] `?` placeholders, no string-interpolated values
- [ ] No `INSERT OR REPLACE` / `lastrowid` / `PRAGMA` / `executescript`
- [ ] Connection closed in `finally` (or is a `_thread_conn`, deliberately not closed)
- [ ] Shared-row writes are atomic / row-locked
- [ ] Passes tests on both backends
- [ ] `_SCHEMA_VERSION` bumped if schema changed
