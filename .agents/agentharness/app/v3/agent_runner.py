"""
agent_runner.py — ArchonHub Agent Execution Engine
====================================================
Executes a single agent dispatch end-to-end:
  1. Load agent skill (DB first, then skill file)
  2. Inject memory + context + tool data
  3. Call LLM
  4. Parse structured JSON output
  5. Write DB updates (any table)
  6. Save run record + memory
  7. Return result to Inez for synthesis

Agent Output Contract (all agents must follow this format):
{
  "response": "Human-readable answer to the task",
  "summary":  "One-sentence summary for Inez",
  "db_writes": [
    {
      "table": "travel_trips|knowledge_base|todos|documents|automations|clients|projects|events_log",
      "op":    "insert|update|upsert",
      "id":    "optional — required for update",
      "data":  { ...fields... }
    }
  ],
  "todos": [
    {"title": "...", "project": "...", "priority": "medium", "description": "..."}
  ],
  "follow_up_agents": [
    {"agent_id": "...", "task": "...", "project": "..."}
  ]
}

Any field may be omitted — the runner handles missing keys gracefully.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE      = Path(__file__).parent
HARNESS   = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
SKILLS_DIR = AGENTS_DIR / "agents" / "projects"

import sys
for _p in (HERE, HARNESS, AGENTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import hub_db as db
    DB_OK = True
except ImportError:
    db = None  # type: ignore
    DB_OK = False

try:
    from hub_nodes import _llm, read_agent_skill_file
    NODES_OK = True
except ImportError:
    NODES_OK = False

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    LC_OK = True
except ImportError:
    LC_OK = False

try:
    from ah_logging import get_logger
    logger = get_logger("agent_runner")
except Exception:
    import logging
    logger = logging.getLogger("agent_runner")

# ---------------------------------------------------------------------------
# Agent system prompt template injected around the agent's own skill content
# ---------------------------------------------------------------------------

_RUNNER_INSTRUCTIONS = """
---
## Output Format (REQUIRED — always respond with valid JSON)

You are an ArchonHub specialist agent. After completing your task, respond ONLY
with a single JSON object in this exact format:

```json
{
  "response": "<your full detailed answer to the task>",
  "summary": "<one sentence summary>",
  "db_writes": [
    {
      "table": "<table name>",
      "op": "insert|update|upsert",
      "id": "<record id if updating>",
      "data": { "<field>": "<value>" }
    }
  ],
  "todos": [
    {"title": "<task title>", "project": "<project slug>", "priority": "medium", "description": "<details>"}
  ],
  "follow_up_agents": [
    {"agent_id": "<agent_id>", "task": "<task description>", "project": "<slug>"}
  ]
}
```

Rules:
- `db_writes` must only use these tables: travel_trips, knowledge_base, todos, documents, projects, clients, automations, events_log
- For `knowledge_base` inserts include: title, content, category, source, project_slug
- For `travel_trips` upserts include: name, destination, depart_date, return_date, status, budget, notes
- For `todos` inserts include: title, description, priority, project
- Omit any section you don't need (empty array or omit key entirely)
- Do NOT wrap response in markdown — return raw JSON only
"""

# ---------------------------------------------------------------------------
# DB write dispatcher
# ---------------------------------------------------------------------------

_ALLOWED_TABLES = {
    "travel_trips", "knowledge_base", "todos", "documents",
    "projects", "clients", "automations", "events_log",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return str(uuid.uuid4())


def _apply_db_write(write: dict) -> bool:
    """Apply a single db_write directive from agent output."""
    if not DB_OK:
        return False

    table = write.get("table", "").strip()
    if table not in _ALLOWED_TABLES:
        logger.warning("agent_runner: blocked db_write to table %r", table)
        return False

    op   = write.get("op", "insert").lower()
    data = write.get("data", {})
    rid  = write.get("id", "")
    if not data:
        return False

    now = _now()

    try:
        with db.get_conn() as conn:
            if table == "travel_trips":
                _write_travel_trip(conn, op, rid, data, now)

            elif table == "knowledge_base":
                _write_knowledge(conn, op, rid, data, now)

            elif table == "todos":
                _write_todo(conn, op, rid, data, now)

            elif table == "documents":
                _write_document(conn, op, rid, data, now)

            elif table == "projects":
                _write_project(conn, op, rid, data, now)

            elif table == "clients":
                _write_client(conn, op, rid, data, now)

            elif table == "events_log":
                _write_event(conn, data, now)

        return True
    except Exception as e:
        logger.error("agent_runner db_write failed table=%s op=%s: %s", table, op, e)
        return False


def _write_travel_trip(conn, op, rid, data, now):
    name = data.get("name", "")
    existing = conn.execute("SELECT id FROM travel_trips WHERE name = ?", (name,)).fetchone() if name else None
    if existing or (op == "update" and rid):
        target_id = rid or existing["id"]
        sets, vals = _build_set(data, ["name", "destination", "depart_date", "return_date",
                                        "status", "budget", "spent", "notes"])
        if sets:
            conn.execute(f"UPDATE travel_trips SET {sets}, updated_at=? WHERE id=?",
                         vals + [now, target_id])
    else:
        conn.execute(
            """INSERT INTO travel_trips
               (id,name,destination,depart_date,return_date,status,budget,spent,notes,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,0,?,?,?)""",
            (_uid(), name, data.get("destination",""), data.get("depart_date",""),
             data.get("return_date",""), data.get("status","planning"),
             float(data.get("budget",0) or 0), data.get("notes",""), now, now),
        )


def _write_knowledge(conn, op, rid, data, now):
    title   = data.get("title","")
    source  = data.get("source","agent")
    cat     = data.get("category","general")
    proj    = data.get("project_slug","")
    content = data.get("content","")
    existing = conn.execute(
        "SELECT id FROM knowledge_base WHERE title=? AND source=?", (title, source)
    ).fetchone()
    if existing:
        conn.execute("UPDATE knowledge_base SET content=?,updated_at=? WHERE id=?",
                     (content, now, existing["id"]))
    else:
        conn.execute(
            """INSERT INTO knowledge_base
               (id,title,content,category,source,project_slug,tags,is_active,created_at,updated_at)
               VALUES (?,?,?,?,?,?,'[]',1,?,?)""",
            (_uid(), title, content, cat, source, proj, now, now),
        )


def _write_todo(conn, op, rid, data, now):
    title = data.get("title","")
    proj  = data.get("project","")
    existing = conn.execute("SELECT id FROM todos WHERE title=? AND project=?", (title, proj)).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO todos
               (id,title,description,priority,status,project,due_date,tags,source,created_at,updated_at)
               VALUES (?,?,?,?,'pending',?,'','[]','agent',?,?)""",
            (_uid(), title, data.get("description",""), data.get("priority","medium"),
             proj, now, now),
        )


def _write_document(conn, op, rid, data, now):
    title = data.get("title","")
    proj  = data.get("project_slug","")
    existing = conn.execute("SELECT id FROM documents WHERE title=? AND project_slug=?", (title,proj)).fetchone()
    if existing:
        conn.execute("UPDATE documents SET content=?,updated_at=? WHERE id=?",
                     (data.get("content",""), now, existing["id"]))
    else:
        conn.execute(
            """INSERT INTO documents
               (id,title,doc_type,content,format,project_slug,client_id,tags,version,status,created_by,created_at,updated_at)
               VALUES (?,?,?,?,'markdown',?,?,'[]',1,'active','agent',?,?)""",
            (_uid(), title, data.get("doc_type","reference"), data.get("content",""),
             proj, data.get("client_id",""), now, now),
        )


def _write_project(conn, op, rid, data, now):
    slug = data.get("slug","")
    existing = conn.execute("SELECT id FROM projects WHERE slug=?", (slug,)).fetchone() if slug else None
    if existing or (op == "update" and rid):
        target_id = rid or existing["id"]
        sets, vals = _build_set(data, ["name","description","status","lead_agent","url","notes"])
        if sets:
            conn.execute(f"UPDATE projects SET {sets}, updated_at=? WHERE id=?", vals + [now, target_id])
    else:
        conn.execute(
            """INSERT INTO projects (id,slug,name,description,status,lead_agent,url,notes,tags,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,'[]',?,?)""",
            (_uid(), slug, data.get("name",""), data.get("description",""),
             data.get("status","active"), data.get("lead_agent",""),
             data.get("url",""), data.get("notes",""), now, now),
        )


def _write_client(conn, op, rid, data, now):
    slug = data.get("slug","")
    existing = conn.execute("SELECT id FROM clients WHERE slug=?", (slug,)).fetchone() if slug else None
    if existing or (op == "update" and rid):
        target_id = rid or existing["id"]
        sets, vals = _build_set(data, ["name","contact_name","contact_email","status","notes"])
        if sets:
            conn.execute(f"UPDATE clients SET {sets}, updated_at=? WHERE id=?", vals + [now, target_id])


def _write_event(conn, data, now):
    conn.execute(
        """INSERT INTO events_log (id,event_type,agent_id,project_slug,payload,created_at)
           VALUES (?,?,?,?,?,?)""",
        (_uid(), data.get("event_type","agent_action"), data.get("agent_id",""),
         data.get("project_slug",""), json.dumps(data.get("payload",{})), now),
    )


def _build_set(data: dict, allowed_fields: list[str]) -> tuple[str, list]:
    """Build SQL SET clause from data dict, only for allowed fields."""
    parts, vals = [], []
    for f in allowed_fields:
        if f in data:
            parts.append(f"{f}=?")
            vals.append(data[f])
    return ", ".join(parts), vals


# ---------------------------------------------------------------------------
# Main executor
# ---------------------------------------------------------------------------

def run_agent(
    agent_id: str,
    task: str,
    project: str = "",
    extra_context: str = "",
    run_id: str | None = None,
    emit: Callable | None = None,
) -> dict:
    """
    Execute one agent:
      - Load skill + memory from DB / skill files
      - Inject context + tool data
      - Call shared LLM
      - Parse structured JSON output
      - Write db_writes + todos to DB
      - Save run record
      Returns:
        {
          "agent_id": str,
          "response": str,       # human-readable output
          "summary": str,        # one sentence
          "db_writes_applied": int,
          "todos_created": int,
          "follow_up_agents": list[dict],
          "error": str | None,
        }
    """
    run_id = run_id or _uid()

    def _emit(evt, **kw):
        if emit:
            try:
                emit(evt, agent_id=agent_id, run_id=run_id, **kw)
            except Exception:
                pass

    _emit("agent_start", task=task[:120])

    if not NODES_OK or not LC_OK:
        return _error_result(agent_id, "hub_nodes / langchain not available")

    # 1. Load skill
    skill_content = ""
    try:
        skill_content, _ = read_agent_skill_file(agent_id)
    except Exception:
        pass
    if not skill_content and DB_OK:
        try:
            skill_content, _ = db.load_skill(agent_id)
        except Exception:
            pass
    if not skill_content:
        skill_content = f"You are {agent_id}, a specialist agent in the ArchonHub portfolio."

    # 2. Load memory context
    memory = ""
    if DB_OK:
        try:
            memory = db.load_memory_context(agent_id) or ""
        except Exception:
            pass

    # 3. Build system prompt
    system = (
        skill_content
        + "\n\n"
        + (f"Memory/Prior context:\n{memory}\n\n" if memory else "")
        + (f"Additional context:\n{extra_context}\n\n" if extra_context else "")
        + _RUNNER_INSTRUCTIONS
    )

    # 4. Call LLM
    _emit("agent_thinking", message=f"{agent_id} working on task...")
    try:
        model = _llm(temperature=0.3)
        response = model.invoke([
            SystemMessage(content=system),
            HumanMessage(content=task),
        ])
        raw = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.error("agent_runner LLM error agent=%s: %s", agent_id, exc)
        return _error_result(agent_id, str(exc))

    # 5. Parse structured output
    parsed = _parse_agent_output(raw)

    # 6. Apply db_writes
    writes_ok = 0
    for write in parsed.get("db_writes", []):
        if _apply_db_write(write):
            writes_ok += 1

    # 7. Apply inline todos
    todos_ok = 0
    for todo in parsed.get("todos", []):
        if todo.get("title") and DB_OK:
            try:
                _apply_db_write({
                    "table": "todos",
                    "op": "insert",
                    "data": todo,
                })
                todos_ok += 1
            except Exception:
                pass

    # 8. Save run record
    if DB_OK:
        try:
            db.save_run({
                "run_id":   run_id,
                "agent_id": agent_id,
                "project":  project,
                "task":     task[:500],
                "output":   parsed.get("response", raw)[:2000],
                "status":   "complete",
                "score":    1.0,
                "graph":    "agent_runner",
            })
        except Exception:
            pass

    # 9. Save memory update
    if DB_OK:
        try:
            db.save_memory(
                agent_id,
                f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                json.dumps({
                    "task":    task[:200],
                    "summary": parsed.get("summary", "")[:200],
                }),
            )
        except Exception:
            pass

    _emit("agent_complete",
          summary=parsed.get("summary","")[:200],
          db_writes=writes_ok,
          todos=todos_ok)

    return {
        "agent_id":           agent_id,
        "response":           parsed.get("response", raw),
        "summary":            parsed.get("summary", ""),
        "db_writes_applied":  writes_ok,
        "todos_created":      todos_ok,
        "follow_up_agents":   parsed.get("follow_up_agents", []),
        "error":              None,
    }


def run_dispatches(
    dispatches: list[dict],
    emit: Callable | None = None,
    max_follow_up_depth: int = 1,
) -> list[dict]:
    """
    Execute a list of Inez dispatch objects. Supports one level of follow-up agents.
    Each dispatch: {"agent_id": str, "task": str, "project": str, "context": str}
    Returns list of results from run_agent().
    """
    results = []
    queue = list(dispatches)

    depth = 0
    while queue and depth <= max_follow_up_depth:
        next_queue = []
        for d in queue:
            agent_id = d.get("agent_id", "")
            task     = d.get("task", "")
            project  = d.get("project", "")
            context  = d.get("context", "")
            if not agent_id or not task:
                continue
            result = run_agent(agent_id, task, project, context, emit=emit)
            results.append(result)
            # Queue any follow-up agents from this result
            for follow in result.get("follow_up_agents", []):
                next_queue.append(follow)
        queue = next_queue
        depth += 1

    return results


def build_synthesis_context(results: list[dict]) -> str:
    """
    Build a context block summarising all agent results, injected into
    Inez's synthesis prompt.
    """
    if not results:
        return ""
    lines = ["[AGENT RESULTS — synthesize these into your response]"]
    for r in results:
        lines.append(f"\n## {r.get('agent_id','unknown')} result")
        lines.append(r.get("response", r.get("summary", "No output")))
        if r.get("db_writes_applied", 0):
            lines.append(f"_(saved {r['db_writes_applied']} record(s) to database)_")
        if r.get("todos_created", 0):
            lines.append(f"_(created {r['todos_created']} new todo(s))_")
        if r.get("error"):
            lines.append(f"⚠️ Error: {r['error']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------

def _parse_agent_output(raw: str) -> dict:
    """Parse agent JSON output, with graceful fallback."""
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Find embedded JSON object
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            data = json.loads(m.group())
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # Fallback — treat full text as response
    return {"response": raw, "summary": raw[:120], "db_writes": [], "todos": []}


def _error_result(agent_id: str, error: str) -> dict:
    return {
        "agent_id":          agent_id,
        "response":          f"Agent {agent_id} encountered an error: {error}",
        "summary":           f"{agent_id} failed: {error[:80]}",
        "db_writes_applied": 0,
        "todos_created":     0,
        "follow_up_agents":  [],
        "error":             error,
    }
