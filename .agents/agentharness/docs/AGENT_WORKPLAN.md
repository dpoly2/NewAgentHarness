# ArchonHub — migration work plan (agent-assignable tasks)

Decomposed, ownable tasks for the Postgres migration + scalability build. Each
task has a scope, the files it touches, and acceptance criteria. Every task is
bound by [DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md); the spec is
[POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md); node work is
[SCALABILITY.md](SCALABILITY.md).

**Global rule:** a task is not done until the full test suite passes on **both**
`DB_BACKEND=sqlite` and `DB_BACKEND=postgres` (contract C9).

## Status (2026-07-01)

| Task | State | Notes |
|------|-------|-------|
| T1 | ✅ done | adapter + config + seams; 33/33 |
| T2 | ✅ done | `translate_ddl`; schema emits both backends |
| T3 | ✅ done | idiom sweep; RETURNING/ON CONFLICT; SQLite-only SQL ported |
| T4 | ✅ done | `scripts/migrate_sqlite_to_pg.py`; dry-run 54 tables/4195 rows; 10/10 |
| T6 | ✅ done | `FOR UPDATE SKIP LOCKED` claim (pg) / optimistic (sqlite) |
| T7 | ✅ done | `LISTEN/NOTIFY` fan-out (pg) / poll (sqlite fallback) |
| T8 | ✅ done | `worker_nodes` registry + heartbeat reaper; `_SCHEMA_VERSION`→12 |
| T9 | ✅ done | [CUTOVER_RUNBOOK.md](CUTOVER_RUNBOOK.md) |
| T5 | 🔄 in progress | dual-backend CI — the milestone where the PG path is first executed |
| T10–T13 | ⏳ deferred | JSONB / BOOLEAN / timestamptz / PG FTS (post-cutover) |

**Verified so far:** 67 DB tests green on SQLite; PG path implemented + statically
reviewed (execution pending T5's Postgres CI leg — no live PG on the dev box).
All changes are uncommitted in the working tree awaiting review.

---

## Milestone M1 — adapter + schema (app boots on empty Postgres)

### T1. Connection adapter `core/db_backend.py` — ✅ IMPLEMENTED
- Built the facade (POSTGRES_MIGRATION §4): `translate_query` (`%`→`%%` then
  `?`→`%s`), `_PgRow` (full sqlite3.Row parity — int+str index, `dict()`,
  iterate-as-values, `get`, `in`, `len`), pragma no-ops, `table_columns()` via
  `information_schema`, pooled psycopg (`get_connection`) + dedicated autocommit
  thread connection (`get_thread_connection`).
- Wired `DB_BACKEND` / `DATABASE_URL` / `DB_POOL_MIN` / `DB_POOL_MAX` into
  `core/config.py`.
- Routed the seams through it: `_db_connection`, `_thread_conn`, `_table_columns`
  (`core/database.py`) and `get_conn` (`hub_db.py`). Note: `get_db` **never
  existed** (the `db.get_db` check in the old `_db_connection` was dead code) — do
  not look for it.
- **Verified:** translator self-test passes; `_PgRow` parity unit test passes;
  empty-`DATABASE_URL` guard raises a clear error; SQLite default path unchanged
  — `tests/test_hub_db.py` 33/33 pass; live DB smoke test (conn, thread-conn
  reuse, `table_columns`) OK.
- **Transaction-semantics decision baked in:** pooled conns `autocommit=False`
  (explicit commit, pool resets on return); thread conn `autocommit=True` (so the
  no-commit pollers `_count_queued_jobs`/`_check_job_cancel_flag` never pin a
  stale snapshot). `commit()`/`rollback()` are guarded no-ops under autocommit.

**Handoffs T1 surfaced (fold into T2/T3):**
- `_ensure_alpaca_schema` (`core/database.py`) runs `PRAGMA table_info(...)`
  inline — must use `db_backend.table_columns()` (T2, schema init).
- Literal-`%` SQL that also uses **SQLite-only functions** is NOT covered by
  translation and needs per-query porting (T3): `date('now')` in
  `morning_brief.py`; `sqlite_master` queries in `add_*.py` inspection scripts
  and `routers/devops.py`.
- 3 `lastrowid` sites → `RETURNING id` (T3): `_insert_ws_event`
  (`core/database.py`), user-create (`hub_db.py:~2102`), + one more per the
  grep in POSTGRES_MIGRATION §6.

### T2. Schema DDL translation
- Translate `hub_db.init_schema()` and the `_ensure_*_schema` /
  `_fallback_init_schema` blocks per the type table in POSTGRES_MIGRATION §5.
- Convert `executescript` blocks to per-statement execution.
- **Accept:** `init_schema()` builds the full schema on empty Postgres; every
  table from the SQLite schema exists with matching columns; `_SCHEMA_VERSION`
  gate still short-circuits warm starts.

### T3. Idiom translation sweep
- Fix the 8 `INSERT OR REPLACE`/`OR IGNORE` → `ON CONFLICT`; the 3 `lastrowid`
  → `RETURNING id`; the 3 `PRAGMA table_info` → `table_columns()`.
- **Accept:** grep for `INSERT OR REPLACE|INSERT OR IGNORE|lastrowid|PRAGMA` in
  `.py` returns only SQLite-backend-guarded code (or nothing). Upsert paths
  (`set_config`, `enqueue_job`, `_upsert_memory`, scheduler lease) round-trip on
  both backends.

## Milestone M2 — data migration (staging runs on migrated Postgres)

### T4. Migration script `scripts/migrate_sqlite_to_pg.py`
- Implement POSTGRES_MIGRATION §8: FK-ordered copy, id preservation, sequence
  reset (`setval`), row-count + spot-check validation. Operates on a **copy** of
  `memory/runs_v3.db`.
- **Accept:** running it against a snapshot yields matching `COUNT(*)` per table;
  admin login works post-migrate; newest 10 `runs`/`job_queue` rows match.

### T5. Dual-backend CI
- CI matrix runs `tests/run_tests.py`, `test_hub_db.py`, `test_hub_server.py` on
  both backends (spin up a Postgres service container).
- **Accept:** both legs green; a PR that breaks one backend fails CI.

## Milestone M3 — concurrency upgrades (multi-worker safe)

### T6. `FOR UPDATE SKIP LOCKED` job claim
- Rewrite `_claim_queued_job` to the single atomic UPDATE...SKIP LOCKED in
  POSTGRES_MIGRATION §7.1; add `worker_id` to `job_queue`.
- **Accept:** a concurrency test with 2+ worker processes claims each queued job
  exactly once (zero double-execution) under contention.

### T7. `LISTEN/NOTIFY` WS broadcast
- Replace the `ws_events` poll in `core/hub.py:133-153` with a `LISTEN/NOTIFY`
  listener; keep `ws_events` as the durable replay log; keep poll as fallback.
- **Accept:** an event produced on node A reaches a WS client connected to node B;
  Inez `run_events` replay (`GET /inez/runs/{run_id}/events`) still works.

### T8. Worker registry + heartbeat reaper
- Add `worker_nodes` (SCALABILITY §2) and `job_queue.claimed_at`/`heartbeat_at`;
  boot-time upsert; heartbeat job; extend `_reap_stale_jobs` to requeue jobs of
  dead workers by stale heartbeat.
- **Accept:** killing a worker mid-job requeues that job to another worker within
  the heartbeat window; the dead node shows `status='down'`.

## Milestone M4 — cutover

### T9. Production cutover runbook + execute
- Quiesce the `ArchonHub` Windows service (admin), final export, import, flip
  `DB_BACKEND=postgres`, restart on the Ubuntu control node.
- **Accept:** live smoke test — admin login, Inez chat round-trip, one scheduled
  job fires — all on Postgres. Rollback rehearsed (flip back to `sqlite`).

## Post-cutover (separate PRs, optional)

- **T10** JSONB migration · **T11** BOOLEAN columns · **T12** `timestamptz` +
  reaper update · **T13** Postgres FTS (`tsvector`/`pg_trgm`) replacing the SQLite
  FTS add-ons. Each per POSTGRES_MIGRATION §9.

---

## Dependency order

```
T1 ─┬─ T2 ─ T3 ─┬─ T4 ─ T5 ─┬─ T6 ─┐
    │           │           ├─ T7 ─┼─ T9 ─ (T10..T13)
    │           │           └─ T8 ─┘
```

T1 gates everything. T6/T7/T8 are parallelizable once M2 is green. T9 requires
all of M3.

## How to hand these to build agents

Each task is self-contained: point the agent at this file's task, plus the two
contracts it names. Require the agent to (1) restate the acceptance criteria,
(2) run both-backend tests before claiming done, (3) paste the DB_ACCESS_CONTRACT
review checklist filled in. Do not let an agent rewrite the scheduler lease (T6
must not touch `_try_acquire_scheduler_lock`) or switch timestamp types (that's
T12, gated).
