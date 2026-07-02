# ArchonHub production / distribution docs

Design and contract docs for taking ArchonHub from a single-box Windows service to
a distributed, highly-available deployment across the mini-PC fleet.

Read in this order:

1. **[HA_DEPLOYMENT_PLAN.md](HA_DEPLOYMENT_PLAN.md)** — the target topology: node
   roles, OS (Ubuntu 24.04), Postgres HA, VIP/LB, rollout phases. Start here.
2. **[POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md)** — the SQLite→Postgres
   migration spec: driver, compatibility adapter, DDL/idiom translation,
   concurrency upgrades, data migration, phasing, rollback.
3. **[DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md)** — binding rules for any code
   that touches the DB. Reviewers reject violations. Non-negotiable.
4. **[SCALABILITY.md](SCALABILITY.md)** — how to add worker / API / DB nodes with
   no downtime; the node registry, autoscaling signals, hard limits.
5. **[AGENT_WORKPLAN.md](AGENT_WORKPLAN.md)** — the work decomposed into
   agent-assignable tasks (T1–T13) with dependency order, acceptance criteria, and
   live status.
6. **[CUTOVER_RUNBOOK.md](CUTOVER_RUNBOOK.md)** — the step-by-step production
   switch from SQLite to Postgres (freeze window, migrate, flip, smoke test,
   rollback).

## Key facts that shaped these docs

- The app is **already multi-worker-aware** (optimistic job claim, stale-job
  reaper, `scheduler_leader` TTL lease, `ws_events` broadcast). It's single-box
  only because the store is SQLite. The migration unlocks the existing design
  across machines — it is not a rearchitecture.
- Migration scope is bounded: 31 files touch `sqlite3`, but through **4
  connection seams**, and the dialect-specific surface is tiny (8
  `INSERT OR REPLACE`, 3 `lastrowid`, 3 `PRAGMA table_info`).
- The **single write primary** is the one thing that doesn't scale horizontally.
  It's the ceiling; guard it and scale it vertically first.
