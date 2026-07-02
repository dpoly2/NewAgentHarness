# ArchonHub — SQLite → Postgres migration spec

Audience: the engineering agents implementing the migration. Read
[DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md) before writing any code — it is
binding. This document is the *what and why*; the contract is the *how you must
write it*.

---

## 0. Why this is smaller than it looks

The app is **already built for many workers sharing one database**. These already
exist in `core/database.py`:

- `_claim_queued_job()` — two-step optimistic job claim (line ~1464)
- `_reap_stale_jobs()` — requeue/fail crashed-worker jobs (line ~1503)
- `_try_acquire_scheduler_lock()` / `_release_scheduler_lock()` — a TTL leader
  lease in `hub_config` (line ~1557), already failover-safe and cross-process
- `ws_events` table + `_insert_ws_event` / `_get_ws_events_since` — DB-backed
  broadcast so any worker can fan out to its WS clients (consumed in
  `core/hub.py:118-153`)

They only work on **one box** today because the store is SQLite (a local file).
Point them at a shared Postgres and they work across machines unchanged. The
migration is therefore: **(a) storage-engine swap, (b) upgrade the SQLite-emulated
concurrency to native Postgres primitives.** It is not a rearchitecture.

## 1. Scope (measured, not guessed)

- 31 `.py` files import/use `sqlite3`, but they reach the DB through **four
  connection seams only**: `get_conn()` (`hub_db.py:119`), `get_db()`,
  `_db_connection()` (`core/database.py:109`), `_thread_conn()`
  (`core/database.py:129`). Fixing the seams fixes most call sites.
- Dialect-specific surface is small: **8** `INSERT OR REPLACE` / `INSERT OR
  IGNORE`, **3** `.lastrowid`, **3** `PRAGMA table_info`, plus `executescript`
  in the two `init_schema` paths and the `PRAGMA journal_mode/...` pragmas.
- Everything else is plain `SELECT/INSERT/UPDATE/DELETE` with `?` placeholders.

## 2. Driver & connection strategy

- **Driver: `psycopg` (v3), synchronous**, with `psycopg_pool.ConnectionPool`.
  Rationale: the codebase is synchronous and thread-based
  (`ThreadPoolExecutor(max_workers=4)` in `agent_runner.run_dispatches`,
  thread-local connections). `asyncpg` would force rewriting every call site.
  Do **not** introduce async here.
- **`_thread_conn()`** (the 4 hot-path pollers) becomes a pool checkout cached in
  thread-local storage, or a dedicated per-thread pool connection. Keep the
  "do not close" contract — return it to the pool on thread exit, not per call.
- **One pool per process**, sized `min=2, max=(worker_threads + a few)`. Set
  `DATABASE_URL` to the HAProxy leader endpoint (see
  [HA_DEPLOYMENT_PLAN.md](HA_DEPLOYMENT_PLAN.md)) so writes always hit the
  primary; failover is transparent to the app.

## 3. Backend switch (config)

Add to `core/config.py`:

```python
DB_BACKEND = os.environ.get("DB_BACKEND", "sqlite")   # "sqlite" | "postgres"
DATABASE_URL = os.environ.get("DATABASE_URL", "")      # postgresql://user:pw@host:5432/archonhub
```

`get_conn()`, `get_db()`, `_db_connection()`, and `_thread_conn()` branch on
`DB_BACKEND`. Both backends must remain runnable so the migration can be
developed and tested against SQLite locally and Postgres in staging. The SQLite
path is removed only after production cutover is signed off.

## 4. The compatibility adapter (lowest-churn path — REQUIRED approach)

Rather than rewrite 31 files, introduce **one** module, `core/db_backend.py`,
exposing a connection facade whose surface matches how the code already uses
`sqlite3.Connection`: `.execute(sql, params) -> cursor`, `cursor.fetchone()`,
`cursor.fetchall()`, `.commit()`, `.close()`, and dict-like rows
(`row["col"]` and `dict(row)` both work).

The facade, when `DB_BACKEND=postgres`, wraps a pooled psycopg connection and:

1. **Translates paramstyle** `?` → `%s`. Verified safe: no SQL string in the
   codebase contains a literal `?` inside quotes and none use `%`. Add a unit
   test asserting this stays true.
2. **Uses `psycopg.rows.dict_row`** so rows behave like `sqlite3.Row`.
3. **No-ops SQLite pragmas** (`journal_mode`, `synchronous`, `cache_size`,
   `temp_store`, `foreign_keys` — FKs are on by default in PG).
4. **Provides `table_columns(table)`** via `information_schema.columns`, replacing
   the 3 `PRAGMA table_info` sites and `_table_columns` (`core/database.py:94`).

`SQLAlchemy Core` is the acceptable *alternative* if the team prefers a
maintained dialect layer, but it is a larger change; the adapter above is the
default. Do not mix both.

## 5. DDL translation rules (SQLite type → Postgres type)

Apply mechanically to the schema in `hub_db.init_schema()` and the
`_ensure_*_schema()` / `_fallback_init_schema()` functions in `core/database.py`:

| SQLite | Postgres | Notes |
|--------|----------|-------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` | affects `runs`, `skills`, `notifications`, `users`, `agent_memory`, `user_preferences`, `events_log`, `ws_events` |
| `TEXT` | `TEXT` | unchanged |
| `REAL` | `DOUBLE PRECISION` | |
| `INTEGER` used as boolean (`is_active`, `read` default 0/1) | **keep `INTEGER`** for the mechanical pass | `_row_to_dict` already bool-coerces these (`core/database.py:154`). Migrate to `BOOLEAN` only in a later hardening phase. |
| JSON-in-`TEXT` (`job_data`, `tags`, `credentials`, `graph_json`, …) | **keep `TEXT`** for the mechanical pass | the `_json_dumps`/`_json_loads` layer is dialect-agnostic. Migrate to `JSONB` later for query power (see §9). |
| `created_at`/`started_at` as ISO `TEXT` | **keep `TEXT`** | `_reap_stale_jobs` relies on lexicographic ISO comparison (`started_at < cutoff_iso`, line ~1542). Keeping TEXT preserves that logic verbatim. Do not switch to `timestamptz` in this pass. |

Rule of thumb for this migration: **change the engine, not the schema shape.**
Type modernization (BOOLEAN, JSONB, timestamptz) is a separate, later PR so the
mechanical migration stays reviewable and reversible.

## 6. Idiom translation

- `INSERT OR REPLACE INTO t (...) VALUES (...)` → `INSERT INTO t (...) VALUES
  (...) ON CONFLICT (<pk>) DO UPDATE SET col = EXCLUDED.col, ...`. The 8 sites
  each have a known primary key (`job_queue.id`, `hub_config.key`, etc.).
- `INSERT OR IGNORE` → `... ON CONFLICT DO NOTHING`.
- `cursor.lastrowid` (3 sites, e.g. `_insert_ws_event` line 1430, `hub_db.py:2102`)
  → append `RETURNING id` and read `cursor.fetchone()["id"]`.
- `conn.executescript(multi;statement;sql)` → execute statements individually.
  `hub_db.init_schema` already holds a `statements` list — iterate it. For the
  `executescript` blocks in `core/database.py`, split on `;` into a list.
- `INSERT ... ON CONFLICT(a, b) DO UPDATE` (already present in hub_db) → valid PG
  as-is; just ensure a matching unique constraint exists.

## 7. Concurrency upgrades (the payoff — do these, don't just emulate)

These replace SQLite workarounds with native Postgres primitives. They are the
reason distribution becomes reliable:

1. **Job claim** — replace the two-step optimistic claim in `_claim_queued_job`
   with a single atomic statement:
   ```sql
   UPDATE job_queue SET status='running', started_at=%s, worker_id=%s
   WHERE id = (
       SELECT id FROM job_queue WHERE status='queued'
       ORDER BY queued_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED
   )
   RETURNING *;
   ```
   `FOR UPDATE SKIP LOCKED` means N workers on N machines never collide and never
   waste a claim attempt. This is the single most important change.
2. **WS broadcast** — replace the `ws_events` poll loop in `core/hub.py:133-153`
   with `LISTEN/NOTIFY`: on insert, `NOTIFY ws_events, '<payload-or-id>'`; each
   API node keeps one dedicated listener connection and forwards to its WS
   clients. Keep the `ws_events` table as the **durable replay log** (Inez run
   events already depend on durable replay). Poll remains as a fallback path.
3. **Scheduler lease** — `_try_acquire_scheduler_lock` already works across
   machines once the DB is shared; **keep it as-is**. Optional later upgrade to
   `pg_advisory_lock`. Do not rewrite it in this migration.
4. **Worker heartbeat + reaper** — add `job_queue.worker_id`, `claimed_at`,
   `heartbeat_at`; workers update `heartbeat_at` periodically; `_reap_stale_jobs`
   keys off stale `heartbeat_at` instead of a fixed 15-min `started_at` window,
   and requeues (`status='queued'`) jobs whose worker vanished. See
   [SCALABILITY.md](SCALABILITY.md) for the node registry this ties into.

## 8. One-time data migration

Script: `scripts/migrate_sqlite_to_pg.py`.

1. Create the Postgres schema (run the PG `init_schema`).
2. Read each SQLite table; bulk-insert into PG in **FK-dependency order**
   (parents first: `tracked_politicians` before `politician_trades`/
   `copy_trade_signals`; `implementation_plans` before `plan_node_events`;
   `conversations` before `messages`; `projects`/`clients` before dependents).
3. Preserve primary keys exactly (including the integer ids).
4. After load, reset identity sequences:
   `SELECT setval(pg_get_serial_sequence('t','id'), MAX(id)) FROM t;` for every
   IDENTITY table, or the migration's next insert collides.
5. **Validate**: assert per-table `COUNT(*)` matches source; spot-check
   `hub_config`, `users` (admin login must still work — see the admin-seed gotcha
   in the project memory), and the newest 10 `runs`/`job_queue` rows.

Run it against a **copy** of `memory/runs_v3.db`, never the live file. The live
DB is written by the `ArchonHub` Windows service — stop/quiesce it (or snapshot
the file) before the authoritative export.

## 9. Deferred hardening (separate PRs, after cutover)

- JSON `TEXT` → `JSONB` (unlocks server-side JSON queries; touch `_json_dumps`/
  `_json_loads` to pass dicts through).
- boolean `INTEGER` → `BOOLEAN`.
- ISO-`TEXT` timestamps → `timestamptz` (update `_reap_stale_jobs` comparison and
  `_now_iso` callers).
- Full-text search: the SQLite FTS add-ons (`add_fts_search.py`) → Postgres
  `tsvector`/`pg_trgm`.

## 10. Phasing & rollback

- **M1** — adapter + PG schema + `DB_BACKEND` switch; app boots on empty PG.
- **M2** — data migration script; app runs on migrated PG in staging, SQLite
  still selectable via env.
- **M3** — concurrency upgrades (§7.1, §7.2, §7.4); multi-worker soak test.
- **M4** — production cutover (quiesce service, final export, import, flip
  `DB_BACKEND=postgres`, restart).
- **Rollback** at any milestone: flip `DB_BACKEND=sqlite`. SQLite path stays in
  the tree until M4 is signed off, so rollback is a config change, not a revert.

## 11. Acceptance criteria

- Full test suite (`tests/run_tests.py`, `test_hub_db.py`, `test_hub_server.py`)
  passes against both backends.
- Two worker processes on two hosts claim disjoint jobs under load (no double
  execution) — the `FOR UPDATE SKIP LOCKED` proof.
- Killing the active control node fails over without losing queued jobs.
- Admin login, Inez chat round-trip, and one scheduled job fire all verified on
  Postgres.
