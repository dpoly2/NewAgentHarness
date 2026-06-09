"""
AgentHarness Hub — Database Layer
hub_db.py

Manages the SQLite database for the Hub server.
Uses the EXISTING runs_v3.db and adds new Hub tables.
WAL mode enabled for concurrent reads from the desktop client.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE       = Path(__file__).parent
HARNESS    = HERE.parent.parent
MEMORY_DIR = HARNESS / "memory"
DATA_DIR   = HARNESS.parent / "data"
DB_PATH    = MEMORY_DIR / "runs_v3.db"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Connection ─────────────────────────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    """Return a new SQLite connection in WAL mode with row_factory."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema bootstrap ──────────────────────────────────────────────────────────
def init_schema():
    """Create all tables (existing + Hub additions). Idempotent."""
    conn = get_db()
    c = conn.cursor()

    # ── Existing tables (kept identical to main_m365.py) ──────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id         TEXT,
            agent_id       TEXT,
            project        TEXT,
            graph          TEXT,
            task           TEXT,
            score          REAL,
            critique       TEXT,
            revision_count INTEGER,
            output         TEXT,
            skill_version  INTEGER,
            status         TEXT,
            created_at     TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id     TEXT,
            skill_name   TEXT,
            version      INTEGER,
            content      TEXT,
            avg_score    REAL,
            last_critique TEXT,
            created_at   TEXT
        )
    """)

    # ── Hub job queue ─────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS job_queue (
            id            TEXT PRIMARY KEY,
            agent_id      TEXT NOT NULL,
            project       TEXT,
            graph         TEXT DEFAULT 'reflexion',
            task          TEXT NOT NULL,
            priority      TEXT DEFAULT 'normal',
            status        TEXT DEFAULT 'queued',
            max_revisions INTEGER DEFAULT 2,
            queued_at     TEXT NOT NULL,
            started_at    TEXT,
            completed_at  TEXT,
            job_data      TEXT
        )
    """)

    # ── Todos ─────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            priority   TEXT DEFAULT 'medium',
            status     TEXT DEFAULT 'pending',
            project    TEXT,
            due_date   TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    # ── Notification history ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            text       TEXT NOT NULL,
            color      TEXT,
            category   TEXT DEFAULT 'system',
            created_at TEXT NOT NULL,
            read       INTEGER DEFAULT 0
        )
    """)

    # ── Hub key/value config store ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS hub_config (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT
        )
    """)

    # ── Scheduled jobs persistence ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id           TEXT PRIMARY KEY,
            agent_id     TEXT NOT NULL,
            project      TEXT,
            graph        TEXT DEFAULT 'reflexion',
            task         TEXT NOT NULL,
            run_type     TEXT DEFAULT 'once',
            cron_expr    TEXT,
            interval_sec INTEGER,
            scheduled_at TEXT,
            next_fire    TEXT,
            status       TEXT DEFAULT 'active',
            created_at   TEXT NOT NULL,
            job_data     TEXT
        )
    """)

    # ── Indices for common queries ────────────────────────────────────────────
    c.execute("CREATE INDEX IF NOT EXISTS idx_runs_agent   ON runs (agent_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_runs_status  ON runs (status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_runs_created ON runs (created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status  ON job_queue (status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_todos_status ON todos (status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_notif_read   ON notifications (read)")

    conn.commit()
    conn.close()
    print("[HubDB] Schema initialized — WAL mode ON")


# ── Run helpers ───────────────────────────────────────────────────────────────
def save_run(r: dict):
    conn = get_db()
    conn.execute(
        """INSERT INTO runs
           (run_id,agent_id,project,graph,task,score,critique,
            revision_count,output,skill_version,status,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            r["run_id"], r["agent_id"], r["project"],
            r.get("graph", "reflexion"), r["task"][:500],
            r["score"], r["critique"], r["revision_count"],
            r["output"][:2000], r["skill_version"],
            r["status"], datetime.now(timezone.utc).isoformat()
        )
    )
    conn.commit()
    conn.close()


def load_runs(limit=100, status=None, agent_id=None, project=None, skip=0):
    conn = get_db()
    clauses, params = [], []
    if status:
        # Support comma-separated: "complete,running"
        statuses = [s.strip() for s in status.split(",")]
        clauses.append(f"status IN ({','.join('?'*len(statuses))})")
        params.extend(statuses)
    if agent_id:
        clauses.append("agent_id = ?"); params.append(agent_id)
    if project:
        clauses.append("project = ?"); params.append(project)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM runs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [limit, skip]
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agent_stats() -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT agent_id, COUNT(*), AVG(score), MAX(score), MAX(created_at) "
        "FROM runs GROUP BY agent_id"
    ).fetchall()
    conn.close()
    return {
        r[0]: {
            "runs":     r[1],
            "avg":      round(r[2] or 0, 2),
            "best":     round(r[3] or 0, 2),
            "last_run": r[4]
        }
        for r in rows
    }


def load_memory_context(agent_id: str) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT score,critique,skill_version,created_at FROM runs "
        "WHERE agent_id=? ORDER BY id DESC LIMIT 1",
        (agent_id,)
    ).fetchone()
    conn.close()
    if row:
        return (f"Last run ({row['created_at'][:10]}): "
                f"score={row['score']:.2f}, skill_v{row['skill_version']}. "
                f"Critique: {row['critique'] or 'none'}")
    return "No prior runs."


# ── Skill helpers ─────────────────────────────────────────────────────────────
def save_skill(agent_id, skill_name, version, content, score, critique):
    conn = get_db()
    conn.execute(
        "INSERT INTO skills (agent_id,skill_name,version,content,avg_score,last_critique,created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (agent_id, skill_name, version, content, score, critique,
         datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def load_skill(skill_name: str) -> tuple:
    conn = get_db()
    row = conn.execute(
        "SELECT content,version FROM skills WHERE skill_name=? ORDER BY version DESC LIMIT 1",
        (skill_name,)
    ).fetchone()
    conn.close()
    return (row["content"], row["version"]) if row else ("", 1)


def list_skills() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT agent_id, skill_name, MAX(version) as version, avg_score "
        "FROM skills GROUP BY agent_id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Job queue helpers ─────────────────────────────────────────────────────────
def enqueue_job(job: dict) -> str:
    job_id = job.get("id") or uuid.uuid4().hex[:8]
    conn = get_db()
    conn.execute(
        """INSERT INTO job_queue
           (id, agent_id, project, graph, task, priority, status, max_revisions, queued_at, job_data)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            job_id,
            job["agent_id"],
            job.get("project", "global"),
            job.get("graph", "reflexion"),
            job["task"],
            job.get("priority", "normal"),
            "queued",
            job.get("max_revisions", 2),
            datetime.now(timezone.utc).isoformat(),
            json.dumps(job)
        )
    )
    conn.commit()
    conn.close()
    return job_id


def update_job_status(job_id: str, status: str, **kwargs):
    conn = get_db()
    sets = ["status = ?"]
    params = [status]
    if status == "running":
        sets.append("started_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
    if status in ("complete", "failed", "cancelled"):
        sets.append("completed_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
    for k, v in kwargs.items():
        sets.append(f"{k} = ?")
        params.append(v)
    params.append(job_id)
    conn.execute(f"UPDATE job_queue SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def load_pending_jobs() -> list:
    """Load queued jobs on Hub restart (for queue recovery)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM job_queue WHERE status = 'queued' ORDER BY "
        "CASE priority WHEN 'urgent' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, queued_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job(job_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM job_queue WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_jobs(status=None, limit=50) -> list:
    conn = get_db()
    if status:
        statuses = [s.strip() for s in status.split(",")]
        rows = conn.execute(
            f"SELECT * FROM job_queue WHERE status IN ({','.join('?'*len(statuses))}) "
            "ORDER BY queued_at DESC LIMIT ?",
            statuses + [limit]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM job_queue ORDER BY queued_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Todo helpers ──────────────────────────────────────────────────────────────
def create_todo(data: dict) -> dict:
    todo_id = data.get("id") or uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO todos (id,title,priority,status,project,due_date,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (todo_id, data["title"], data.get("priority","medium"),
         data.get("status","pending"), data.get("project"),
         data.get("due_date"), now, now)
    )
    conn.commit()
    conn.close()
    return get_todo(todo_id)


def get_todo(todo_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_todos(status=None, priority=None) -> list:
    conn = get_db()
    clauses, params = [], []
    if status:    clauses.append("status = ?");   params.append(status)
    if priority:  clauses.append("priority = ?"); params.append(priority)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM todos {where} ORDER BY "
        "CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
        "WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_todo(todo_id: str, data: dict) -> dict | None:
    allowed = {"title", "priority", "status", "project", "due_date"}
    sets, params = [], []
    for k, v in data.items():
        if k in allowed:
            sets.append(f"{k} = ?"); params.append(v)
    if not sets:
        return get_todo(todo_id)
    sets.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(todo_id)
    conn = get_db()
    conn.execute(f"UPDATE todos SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return get_todo(todo_id)


def delete_todo(todo_id: str) -> bool:
    conn = get_db()
    cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def migrate_todos_json():
    """One-time migration: import todos.json into SQLite if not already done."""
    todos_json = DATA_DIR / "todos.json"
    if not todos_json.exists():
        return
    marker = DATA_DIR / ".todos_migrated"
    if marker.exists():
        return
    try:
        todos = json.loads(todos_json.read_text())
        for t in todos:
            if t.get("title"):
                create_todo(t)
        marker.touch()
        print(f"[HubDB] Migrated {len(todos)} todos from todos.json → SQLite")
    except Exception as e:
        print(f"[HubDB] Todo migration error: {e}")


# ── Notification helpers ──────────────────────────────────────────────────────
def save_notification(text: str, color: str = None, category: str = "system"):
    conn = get_db()
    conn.execute(
        "INSERT INTO notifications (text,color,category,created_at) VALUES (?,?,?,?)",
        (text, color, category, datetime.now(timezone.utc).isoformat())
    )
    # Keep last 1000 only
    conn.execute(
        "DELETE FROM notifications WHERE id NOT IN "
        "(SELECT id FROM notifications ORDER BY id DESC LIMIT 1000)"
    )
    conn.commit()
    conn.close()


def list_notifications(limit=100, unread_only=False) -> list:
    conn = get_db()
    where = "WHERE read = 0" if unread_only else ""
    rows = conn.execute(
        f"SELECT * FROM notifications {where} ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notifications_read():
    conn = get_db()
    conn.execute("UPDATE notifications SET read = 1")
    conn.commit()
    conn.close()


def clear_notifications():
    conn = get_db()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    conn.close()


# ── Config helpers ────────────────────────────────────────────────────────────
def get_config(key: str, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM hub_config WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default


def set_config(key: str, value):
    conn = get_db()
    conn.execute(
        "INSERT INTO hub_config (key,value,updated_at) VALUES (?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, json.dumps(value), datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


# ── Briefing cache ────────────────────────────────────────────────────────────
def cache_briefing(data: dict):
    set_config("briefing_cache", data)


def get_briefing_cache() -> dict | None:
    return get_config("briefing_cache")


# ── Scheduled job helpers ─────────────────────────────────────────────────────
def save_scheduled_job(job: dict) -> str:
    job_id = job.get("id") or uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO scheduled_jobs
           (id,agent_id,project,graph,task,run_type,cron_expr,interval_sec,
            scheduled_at,next_fire,status,created_at,job_data)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (job_id, job["agent_id"], job.get("project","global"),
         job.get("graph","reflexion"), job["task"],
         job.get("run_type","once"), job.get("cron_expr"),
         job.get("interval_sec"), job.get("scheduled_at"),
         job.get("next_fire"), job.get("status","active"),
         job.get("created_at", now), json.dumps(job))
    )
    conn.commit()
    conn.close()
    return job_id


def list_scheduled_jobs(status="active") -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM scheduled_jobs WHERE status = ? ORDER BY next_fire ASC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_scheduled_job(job_id: str) -> bool:
    conn = get_db()
    cur = conn.execute("UPDATE scheduled_jobs SET status='cancelled' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


if __name__ == "__main__":
    init_schema()
    migrate_todos_json()
    print(f"[HubDB] Database ready at {DB_PATH}")
