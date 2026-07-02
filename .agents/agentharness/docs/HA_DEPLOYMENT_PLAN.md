# ArchonHub — HA Production Deployment Plan

> Part of the [production/distribution doc set](README.md). Companion docs:
> [POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md) ·
> [DB_ACCESS_CONTRACT.md](DB_ACCESS_CONTRACT.md) ·
> [SCALABILITY.md](SCALABILITY.md) · [AGENT_WORKPLAN.md](AGENT_WORKPLAN.md)

**Target:** distribute ArchonHub across 5 mini PCs on Ubuntu Server 24.04 LTS with a
highly-available control plane and a horizontally-scaled worker pool.

**Hardware:** 3× HP Elite Mini 800 G9 (one full-storage, two with a single 256 GB drive),
2× Dell OptiPlex 7080 Micro. All CPU-only (no usable GPU).

---

## 1. Why it splits into two tiers

ArchonHub today is a single-node monolith. Three properties block naive N-way replication:

- **State is SQLite** (`core/database.py`, thread-local conns, job queue via `_claim_queued_job`).
  SQLite is single-machine — no multi-writer over a network. **This is the hard blocker.**
- **Scheduler is single-owner** (`HubScheduler`, `_JOB_SPECS`, commit `6eb3b8f`). Exactly one
  node may run built-in jobs.
- **Bottleneck is CPU-bound Ollama inference** (~17 tok/s). This is the part worth scaling.

So the design is:

- **Control plane** (state + scheduler + API): authoritative on one active node, warm standby,
  automatic failover. Made *reliable*.
- **Worker pool** (Ollama + agent runners): stateless, pull jobs. Scaled *out*.

## 2. Node role map

| Node | Hardware | Role |
|------|----------|------|
| cp1 | HP 800 G9, large storage | Control plane active — API + scheduler (leader) + Postgres primary |
| cp2 | HP 800 G9, large storage | Control plane standby — API (idle) + Postgres replica |
| w1  | HP 800 G9, 256 GB | Worker — Ollama + agent runner + etcd |
| w2  | Dell 7080 Micro | Worker — Ollama + agent runner + etcd |
| w3  | Dell 7080 Micro | Worker — Ollama + agent runner + etcd + reverse proxy |

State on the big drives; inference on the small ones (Ollama models are 2–8 GB each).

## 3. Infrastructure stack

- **OS:** Ubuntu Server 24.04 LTS, headless, SSH keys only, `ufw`, `chrony` (time sync is
  required for etcd / Patroni / advisory-lock correctness).
- **Provisioning:** Ansible (fixed 5-node fleet — k3s is overkill; Compose + Ansible is more
  debuggable). One Docker image, role selected by `ROLE=api|worker` env.
- **Postgres HA:** Patroni on cp1/cp2 + a 3-node **etcd** on w1/w2/w3 (quorum lives off the DB
  nodes, prevents split-brain). Automatic failover: cp1 down → cp2 promoted.
  - *Simpler alternative if Patroni is too much:* primary/replica + `repmgr` with manual/scripted
    promotion. Accepts a few minutes of downtime on cp1 loss. **Recommended to start here**,
    add Patroni later.
- **VIP + routing:** `keepalived` floating IP for the client endpoint; **HAProxy** routes
  Postgres 5432 → current leader via Patroni REST health check; **Caddy** terminates client TLS.
- **Backups:** `pgBackRest` — WAL archiving + nightly full to a second box / NAS + offsite copy.
- **Monitoring:** Uptime Kuma (light) + optional `node_exporter`/Prometheus.

### Firewall / ports
API 8765 (internal), Postgres 5432, Patroni 8008, etcd 2379/2380, Ollama 11434,
VRRP (keepalived), 443 (Caddy → clients).

## 4. Application engineering backlog (critical path first)

1. **SQLite → Postgres.** Rework `core/database.py`: replace `_thread_conn()` with a connection
   pool (asyncpg/SQLAlchemy); port schema (`_SCHEMA_VERSION = 11`) + migrations; convert
   `AUTOINCREMENT` → `IDENTITY`, drop SQLite-isms. **Biggest lift, gates everything.**
   One-time export/import script to migrate live data.
2. **Job queue → `SELECT … FOR UPDATE SKIP LOCKED`** (replacing `_claim_queued_job` polling).
   Add `worker_id`, `claimed_at`, `heartbeat`. The existing job reaper (commit `6eb3b8f`)
   requeues stale claims.
3. **Standalone worker process** (`agent_worker.py`): claim job → `hub_nodes.run_graph` on
   **localhost** Ollama → write result → `NOTIFY`. Run N per worker node (N ≈ core budget).
4. **Scheduler leader election:** `pg_try_advisory_lock` in `HubScheduler` startup; only the
   lock holder runs `_JOB_SPECS`; standby retries. On failover the new API node takes the lock.
5. **WebSocket fan-out:** Postgres `LISTEN/NOTIFY` on `inez_response` + run-event channels. The
   node holding a client WS listens and forwards. The durable `run_events` log already exists,
   so replay (`GET /inez/runs/{run_id}/events`) still works.
6. **Shared config/secrets:** render `.agents/.env` per node via Ansible Vault. `JWT_SECRET` and
   `ADMIN_PASSWORD` must be identical on all API nodes. DB config table is already shared.
7. **File storage:** if `knowledge_base`/`documents` write to disk, move to NFS (from cp1) or
   MinIO (on workers). If already DB-backed, no change.
8. **Health endpoints:** `/healthz` (liveness), `/readyz` (DB reachable + leader status) for
   HAProxy / keepalived checks.
9. **Interactive Ollama routing:** agent workers use localhost Ollama. The control-plane Inez
   interactive path load-balances across worker Ollama endpoints via `llm_router`
   (least-busy / round-robin).

## 5. Failure behavior

- **cp1 (active) dies:** Patroni promotes cp2 Postgres; keepalived moves the VIP; cp2 API acquires
  the scheduler advisory lock; workers reconnect through HAProxy. In-flight jobs reaped + requeued.
- **A worker dies:** its claimed jobs reaped after heartbeat timeout and requeued elsewhere.
  Throughput drops, no outage.
- **Network partition:** 3-node etcd quorum on workers keeps the majority side authoritative;
  minority steps down (no split-brain).

## 6. Rollout order

- **2a — Postgres foundation:** Ubuntu on all 5, Ansible baseline, Docker, etcd, Patroni
  (primary/replica). Migrate DB off SQLite. Run app single-instance against Postgres. Validate.
- **2b — Distribute workers:** split out `agent_worker.py`; run 3 workers pulling the queue;
  agent runs go parallel across nodes.
- **3a — Second API + scheduler lock + LISTEN/NOTIFY** WS fan-out on cp2.
- **3b — Edge HA:** keepalived VIP + HAProxy leader routing + Caddy TLS. **Test: kill cp1.**
- **4 — Ops:** pgBackRest backups, monitoring, runbooks.

## 7. Open risks / decisions

- The **SQLite→Postgres migration** is the critical path and touches many files — build a test
  harness first. Highest risk.
- **Patroni+etcd vs simple repmgr:** start with repmgr (manual promotion) to reduce operational
  complexity; graduate to Patroni auto-failover once the rest is stable.
- **CPU-only ceiling:** distribution improves throughput and reliability, not per-call latency.
  Consider a real remote provider (Anthropic API key) for the *interactive* Inez path while
  keeping local Ollama for batch agent runs — the Inez timeout notes already flag that Inez needs
  a real remote provider for good speed.
