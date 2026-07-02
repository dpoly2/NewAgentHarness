# ArchonHub — scalability & adding systems

How to add capacity to the deployment — extra worker nodes, extra control-plane
nodes, or extra API front-ends — without downtime or code changes. Depends on the
Postgres migration ([POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md)) being done;
until then the app is single-box.

Companion docs: [HA_DEPLOYMENT_PLAN.md](HA_DEPLOYMENT_PLAN.md) (topology),
[DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md) (multi-node rules).

---

## 1. The scaling model

Three independently scalable tiers. Know which one you're short on before adding
hardware:

| Tier | What it does | Scale when | How to scale |
|------|--------------|-----------|--------------|
| **Workers** | claim jobs, run agent graphs on local Ollama | queue backlog / latency grows | add worker nodes (horizontal, linear) |
| **API front-ends** | serve HTTP + WebSocket | request/WS concurrency grows | add API nodes behind the LB |
| **Control DB** | Postgres primary + replicas | read load or HA needs grow | add read replicas; scale primary vertically |

The **primary Postgres is the one thing you cannot horizontally scale for
writes.** It is the ceiling. Everything else adds linearly. Keep the primary on
your beefiest box and vertically scale it (RAM, NVMe) before worrying about the
rest.

## 2. Worker node registry (build this)

Add a table so the cluster knows what nodes exist and whether they're alive:

```sql
CREATE TABLE IF NOT EXISTS worker_nodes (
    id             TEXT PRIMARY KEY,        -- stable node id (hostname or uuid)
    hostname       TEXT NOT NULL,
    role           TEXT NOT NULL,           -- 'worker' | 'api' | 'control'
    capacity       INTEGER DEFAULT 1,       -- max concurrent jobs this node runs
    ollama_url     TEXT DEFAULT '',         -- reachable inference endpoint
    status         TEXT DEFAULT 'active',   -- 'active' | 'draining' | 'down'
    last_heartbeat TEXT,                    -- ISO UTC, per DB_ACCESS_CONTRACT C6
    started_at     TEXT
);
```

- On boot, each process **upserts** its row (`ON CONFLICT (id) DO UPDATE`).
- A background job updates `last_heartbeat` every ~10s.
- The reaper marks nodes `down` when `last_heartbeat` is stale and requeues their
  in-flight `job_queue` rows (`worker_id` → back to `status='queued'`).
- Admin/`/healthz` surfaces the live roster.

This is what turns "add a box" into a zero-touch operation: a new worker appears
in the registry and starts claiming; a dead worker's jobs get requeued.

## 3. Adding a worker node (the common case)

Fully additive — no code change, no restart of existing nodes:

1. Install Ubuntu + Docker via the Ansible baseline; add the node to the
   inventory.
2. Pull the ArchonHub image; deploy with `ROLE=worker`,
   `DATABASE_URL=<HAProxy leader VIP>`, `OLLAMA_URL=http://localhost:11434`.
3. `ollama pull` the model set the agents use.
4. Container boots → registers in `worker_nodes` → starts
   `_claim_queued_job()` (`FOR UPDATE SKIP LOCKED`, so it safely competes with
   existing workers) → throughput rises immediately.

To remove one: set its `status='draining'` (stops new claims, lets current jobs
finish), then power off. The reaper handles a hard death too.

## 4. Adding an API front-end

1. Deploy the image with `ROLE=api`, same `DATABASE_URL`, same `JWT_SECRET` /
   `ADMIN_PASSWORD` (contract C11 — tokens must validate on any node).
2. Add it to the HAProxy/Caddy backend pool with a `/readyz` health check.
3. WebSocket correctness comes from Postgres `LISTEN/NOTIFY` (POSTGRES_MIGRATION
   §7.2): a job running on any node publishes `inez_response`, and whichever API
   node holds the client's socket forwards it. No sticky sessions required. If
   `LISTEN/NOTIFY` isn't in yet, enable sticky sessions at the LB as a stopgap.

## 5. Adding a Postgres replica

1. Provision the node; `pgBackRest`/`pg_basebackup` from the primary; start as a
   streaming standby.
2. Register with Patroni/repmgr so it participates in failover.
3. Point read-only workloads (reports, analytics, dashboards) at a replica via a
   separate read `DATABASE_URL_RO` to offload the primary. **Writes always go to
   the primary** through the LB leader route.

## 6. Autoscaling signal (when to add, programmatically)

Drive capacity decisions off metrics the app already exposes or can cheaply add:

- **Queue depth**: `_count_queued_jobs()` sustained above `sum(worker capacity)`
  for N minutes → add a worker.
- **Queue latency**: time from `queued_at` to `started_at` (p95) crossing an SLA
  → add a worker.
- **Reaper rate**: rising stale-job reaps → a worker is unhealthy, not
  under-provisioned; investigate before adding.
- **DB primary CPU / connection saturation** → scale the DB vertically or add
  replicas; do **not** add workers (they'd worsen it).

For a 5-node homelab this is a dashboard + manual `ansible-playbook add-worker`.
The registry + metrics make true autoscaling (a controller that provisions nodes)
a later, optional step.

## 7. Capacity planning rule of thumb

- Per-node job throughput ≈ `capacity` × (1 / mean_graph_seconds), and
  `mean_graph_seconds` is dominated by CPU-only Ollama inference. Measure it per
  model on the target hardware — do not assume.
- Set each node's `capacity` to roughly `physical_cores / threads_per_inference`
  so you don't oversubscribe and thrash. Start at `capacity=2` on the mini PCs
  and tune from queue latency.
- Interactive Inez latency does **not** improve by adding workers — it's a single
  call's wall-clock. For that, use a real remote provider (see
  HA_DEPLOYMENT_PLAN §7); reserve local Ollama workers for batch agent runs.

## 8. Hard limits to remember

- **Single write primary.** All the horizontal scale in the world still funnels
  writes through one Postgres. Guard it.
- **One scheduler leader.** Only the lease-holder runs built-in jobs, by design
  (contract C8). Adding nodes does not add schedulers.
- **Shared file storage** must scale with document/knowledge volume (NFS export
  or MinIO) — adding workers doesn't add file capacity.
