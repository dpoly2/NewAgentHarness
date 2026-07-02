# ArchonHub — Postgres cutover runbook (T9 / migration M4)

The step-by-step to switch the live ArchonHub from SQLite to Postgres. This is the
DB-engine cutover; it works whether the server is still the Windows `ArchonHub`
service or already the Ubuntu control node. Do it in a scheduled freeze window.

Companion docs: [POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md) (§8 data migration,
§10 phasing/rollback), [HA_DEPLOYMENT_PLAN.md](HA_DEPLOYMENT_PLAN.md),
[DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md).

> **Rollback is a config flip.** Until this runbook is signed off, `DB_BACKEND`
> stays switchable and the SQLite file is left intact. If anything looks wrong,
> set `DB_BACKEND=sqlite` and restart — you're back on the old store in seconds.

---

## 0. Preconditions (verify BEFORE the window)

- [ ] T1–T8 merged; the dual-backend CI (T5) is green on **both** legs.
- [ ] Postgres is up and reachable (primary + replica per HA plan), and the app's
      `DATABASE_URL` target resolves (through the HAProxy leader route if HA is on).
- [ ] `psycopg[binary]` + `psycopg_pool` installed in the server's Python env.
- [ ] A **rehearsed** dry run of `scripts/migrate_sqlite_to_pg.py` against a recent
      snapshot succeeded (count parity PASS). Do not first-run the migration during
      the window.
- [ ] You have admin rights to restart the service (Windows: elevated PowerShell —
      the `ArchonHub` nssm service refuses non-admin control; Ubuntu: sudo).
- [ ] Announce the freeze window to users.

## 1. Quiesce the writer (start of freeze)

The SQLite file must stop changing so the export is a consistent point-in-time.

- **Windows (current):** elevated PowerShell →
  `Restart-Service ArchonHub -Force` is NOT what you want here; instead **stop** it:
  `Stop-Service ArchonHub -Force` (or `nssm stop ArchonHub`). Confirm no orphan
  `hub_server.py` is holding the DB (`Get-Process python*`).
- **Ubuntu:** `sudo systemctl stop archonhub`.

Freeze begins now. Keep it short — every minute of freeze is data the SQLite file
holds that isn't yet in Postgres.

## 2. Snapshot the SQLite DB

Never migrate from the live file. Copy it:

```
# from a stopped state
cp .agents/agentharness/memory/runs_v3.db  <snapshot-dir>/runs_v3.cutover.db
```

Keep this snapshot — it is also your rollback reference for what was migrated.

## 3. Run the migration

```
cd .agents/agentharness/app/v3
# dry-run first for a final sanity read (no PG writes)
python scripts/migrate_sqlite_to_pg.py --sqlite <snapshot-dir>/runs_v3.cutover.db --dry-run
# real load into Postgres (DATABASE_URL from env / .agents/.env)
DB_BACKEND=postgres python scripts/migrate_sqlite_to_pg.py --sqlite <snapshot-dir>/runs_v3.cutover.db
```

The script creates the PG schema via the app's own `_init_schema()`, copies all
tables in FK order preserving ids, resets IDENTITY sequences, and validates row
counts. **It exits non-zero on any count mismatch — treat a non-zero exit as a
STOP.** Note: SQLite FTS shadow tables are intentionally skipped; PG full-text is
rebuilt later (task T13), so search is empty until then — expected.

## 4. Flip the backend

Edit `.agents/.env` (env is loaded from there, not the v3 dir):

```
DB_BACKEND=postgres
DATABASE_URL=postgresql://archonhub:<pw>@<leader-host>:5432/archonhub
```

Confirm `JWT_SECRET` and `ADMIN_PASSWORD` are set and identical to what the old
instance used (tokens/admin login depend on them — see the admin-seed gotcha in
project memory: the seed only applies to an empty `users` table, which the
migrated DB is not).

## 5. Restart and bring workers up

- **Windows:** elevated → `Start-Service ArchonHub` (or `nssm start ArchonHub`).
- **Ubuntu:** `sudo systemctl start archonhub`; then start the worker nodes
  (`ROLE=worker`, same `DATABASE_URL`) — they register in `worker_nodes` and begin
  claiming via `FOR UPDATE SKIP LOCKED`.

Freeze ends once smoke tests (next) pass.

## 6. Smoke test (gate — all must pass)

- [ ] **Startup clean:** logs show schema at v12, no `SystemExit` from the security
      gate, no psycopg pool errors. `worker_nodes` shows the live node(s).
- [ ] **Admin login** works (proves `users` migrated + password hashing intact).
- [ ] **Inez chat** round-trips: POST returns `202`, and the answer arrives over the
      WebSocket (proves `LISTEN/NOTIFY` fan-out on PG, not just the poll fallback).
- [ ] **Job execution:** submit an agent job; confirm exactly one worker claims it
      (no double-run) and it completes; `runs` row written.
- [ ] **Scheduler:** one built-in `_JOB_SPECS` job fires on the leader only.
- [ ] **Data spot-check:** newest 10 `runs`/`job_queue`, `hub_config` count, a few
      `messages`/`projects` match the pre-cutover values.
- [ ] **Reaper/heartbeat:** kill a worker mid-job; within the heartbeat window the
      job requeues and the node shows `status='down'`.

If any fail → **§8 rollback**.

## 7. Post-cutover (after sign-off)

- Take a fresh `pgBackRest`/`pg_dump` baseline of the migrated PG.
- Keep the SQLite snapshot archived for at least one week.
- Schedule the deferred hardening PRs (POSTGRES_MIGRATION §9 / tasks T10–T13:
  JSONB, BOOLEAN, timestamptz, Postgres FTS).
- Only after a stable soak: remove the SQLite branch from the codebase.

## 8. Rollback

If the smoke test fails or production misbehaves within the soak:

1. Stop the service (§1).
2. Revert `.agents/.env`: `DB_BACKEND=sqlite` (leave `DATABASE_URL` in place, it's
   ignored on the sqlite path).
3. Start the service (§5, control node only).

You are back on the original SQLite file. **Caveat:** any writes made to Postgres
after the flip (§4) are not in the SQLite file — they are lost on rollback. This is
why the freeze window matters and why rollback should be decided fast, before real
user writes accumulate on PG. If significant PG writes have occurred and you must
roll back, migrate those deltas back manually before reopening to users.

## 9. Freeze-window checklist (print this)

```
[ ] users announced        [ ] service stopped        [ ] snapshot taken
[ ] dry-run PASS           [ ] migration PASS (exit 0)[ ] .env flipped
[ ] JWT/ADMIN verified     [ ] service + workers up   [ ] smoke tests PASS
[ ] fresh PG backup        [ ] window closed
```
