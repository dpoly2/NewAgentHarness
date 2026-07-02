"""Plan inbox autoloader.

Watches .agents/agentharness/plans/inbox/ for .yaml / .yml / .json files.
Each file is parsed as a plan, imported via the same logic as POST /api/plans/from-yaml,
then moved to plans/processed/ (success) or plans/failed/ (parse error).

Entry points
------------
scan_plan_inbox()        — sync, safe to call from a thread or async via asyncio.to_thread
async_scan_plan_inbox()  — async wrapper (awaitable from FastAPI lifespan or scheduler)

Deduplication
-------------
A lightweight manifest file (plans/inbox/.processed_manifest) records SHA-256 hashes
of every file ever processed so re-drops of the same file are skipped without a DB query.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

try:
    from ah_logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("plan_autoload")

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent.parent  # app/v3/
_AGENTS_DIR = _HERE.parent.parent      # .agents/
PLAN_BASE_DIR   = _AGENTS_DIR / "plans"
PLAN_INBOX_DIR  = PLAN_BASE_DIR / "inbox"
PLAN_PROCESSED_DIR = PLAN_BASE_DIR / "processed"
PLAN_FAILED_DIR    = PLAN_BASE_DIR / "failed"
_MANIFEST_FILE     = PLAN_INBOX_DIR / ".processed_manifest"

_SUPPORTED_SUFFIXES = {".yaml", ".yml", ".json"}


def _ensure_dirs() -> None:
    for d in (PLAN_INBOX_DIR, PLAN_PROCESSED_DIR, PLAN_FAILED_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _load_manifest() -> set[str]:
    """Return set of SHA-256 hex digests already processed."""
    if not _MANIFEST_FILE.exists():
        return set()
    try:
        return set(json.loads(_MANIFEST_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_manifest(seen: set[str]) -> None:
    try:
        _MANIFEST_FILE.write_text(json.dumps(sorted(seen)), encoding="utf-8")
    except Exception:
        pass


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _parse_yaml_plan(data: dict, filename: str) -> Optional[dict]:
    """Convert a raw dict (from YAML/JSON) into a plan dict.
    Returns None and logs an error on validation failure."""
    title = str(data.get("title", "")).strip()
    objective = str(data.get("objective", "")).strip()
    if not title or not objective:
        logger.error("plan_autoload: %s missing 'title' or 'objective' — skipping", filename)
        return None

    raw_nodes = data.get("nodes", [])
    if not raw_nodes:
        logger.error("plan_autoload: %s has no nodes — skipping", filename)
        return None

    nodes = []
    for n in raw_nodes:
        if not isinstance(n, dict):
            continue
        node_id = str(n.get("id", "")).strip()
        if not node_id:
            continue
        nodes.append({
            "id": node_id,
            "label": str(n.get("label", node_id)),
            "role": str(n.get("role", "work")),
            "purpose": str(n.get("purpose", "")),
            "context": str(n.get("context", "")),
            "agent_id": str(n.get("agent", n.get("agent_id", "human"))),
            "allowed_scope": list(n.get("scope", n.get("allowed_scope", []))),
            "depends_on": list(n.get("deps", n.get("depends_on", []))),
            "entry_criteria": list(n.get("entry", n.get("entry_criteria", []))),
            "exit_criteria": list(n.get("exit", n.get("exit_criteria", []))),
            "expected_evidence": list(n.get("evidence", n.get("expected_evidence", []))),
            "on_fail": str(n.get("on_fail", "block")),
            "retry_limit": int(n.get("retry_limit", 1)),
            "status": "pending", "started_at": None, "completed_at": None,
            "assigned_run_id": None, "evidence": [], "blocked_reason": None,
            "drift_notes": None, "attempt": 0,
        })

    if not nodes:
        logger.error("plan_autoload: %s — no valid nodes parsed", filename)
        return None

    raw_edges = data.get("edges", [])
    edges = []
    if raw_edges:
        for e in raw_edges:
            edges.append({
                "id": f"{e.get('from')}__{e.get('to')}",
                "from_node": str(e.get("from", "")),
                "to_node": str(e.get("to", "")),
                "kind": str(e.get("kind", "sequence")),
                "condition": e.get("condition"),
                "parallel_group": e.get("parallel_group"),
                "handoff_context": e.get("handoff_context"),
            })
    else:
        # Auto-generate edges from depends_on
        node_ids = {n["id"] for n in nodes}
        for node in nodes:
            for dep in node.get("depends_on", []):
                if dep in node_ids:
                    edges.append({
                        "id": f"{dep}__{node['id']}",
                        "from_node": dep, "to_node": node["id"],
                        "kind": "dependency",
                        "condition": None, "parallel_group": None, "handoff_context": None,
                    })

    from core.database import _now_iso
    entry = nodes[0]["id"] if nodes else ""
    return {
        "plan_id": uuid.uuid4().hex,
        "title": title, "version": 1,
        "authored_by": str(data.get("authored_by", "autoload")),
        "created_at": _now_iso(), "updated_at": _now_iso(),
        "objective": objective,
        "project": str(data.get("project", "")),
        "constraints": list(data.get("constraints", [])),
        "nodes": nodes, "edges": edges, "entry_node": entry,
        "status": "draft",
        "preflight_report": None, "run_id": None,
        "tags": list(data.get("tags", [])),
        "completed_at": None, "abandoned_reason": None,
        "drift_proposals": [], "current_drift_proposal_id": None,
        "_source_file": filename,
    }


def scan_plan_inbox() -> list[dict]:
    """Scan inbox, import new plans, move files. Returns list of result dicts.

    Each result: {"file": str, "status": "imported"|"skipped"|"failed", "plan_id": str|None, "error": str|None}
    """
    _ensure_dirs()
    seen = _load_manifest()
    results = []

    candidates = sorted(
        p for p in PLAN_INBOX_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in _SUPPORTED_SUFFIXES
    )

    if not candidates:
        return results

    logger.info("plan_autoload: scanning %d file(s) in inbox", len(candidates))

    try:
        from core.database import _save_plan, _append_plan_event, _now_iso
        DB_OK = True
    except ImportError:
        DB_OK = False
        logger.error("plan_autoload: core.database not available — aborting scan")
        return results

    for path in candidates:
        fname = path.name
        try:
            digest = _file_hash(path)
        except Exception as exc:
            results.append({"file": fname, "status": "failed", "plan_id": None, "error": f"hash error: {exc}"})
            continue

        if digest in seen:
            logger.debug("plan_autoload: %s already processed (hash match) — skipping", fname)
            results.append({"file": fname, "status": "skipped", "plan_id": None, "error": None})
            continue

        # Parse
        raw_data = None
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                raw_data = json.loads(text)
            else:
                try:
                    import yaml as _yaml
                    raw_data = _yaml.safe_load(text)
                except ImportError:
                    # Fallback: try json anyway
                    raw_data = json.loads(text)
        except Exception as exc:
            err = f"parse error: {exc}"
            logger.error("plan_autoload: %s — %s", fname, err)
            _move(path, PLAN_FAILED_DIR / f"{path.stem}__{digest[:8]}{path.suffix}")
            seen.add(digest)
            results.append({"file": fname, "status": "failed", "plan_id": None, "error": err})
            continue

        if not isinstance(raw_data, dict):
            err = "top-level must be a YAML/JSON mapping"
            logger.error("plan_autoload: %s — %s", fname, err)
            _move(path, PLAN_FAILED_DIR / f"{path.stem}__{digest[:8]}{path.suffix}")
            seen.add(digest)
            results.append({"file": fname, "status": "failed", "plan_id": None, "error": err})
            continue

        plan = _parse_yaml_plan(raw_data, fname)
        if plan is None:
            _move(path, PLAN_FAILED_DIR / f"{path.stem}__{digest[:8]}{path.suffix}")
            seen.add(digest)
            results.append({"file": fname, "status": "failed", "plan_id": None, "error": "validation failed"})
            continue

        # Save to DB
        try:
            _save_plan(plan)
            _append_plan_event(plan["plan_id"], None, "plan.created", {
                "title": plan["title"],
                "authored_by": plan["authored_by"],
                "source": "autoload",
                "source_file": fname,
            })
        except Exception as exc:
            err = f"db save error: {exc}"
            logger.error("plan_autoload: %s — %s", fname, err)
            results.append({"file": fname, "status": "failed", "plan_id": None, "error": err})
            continue

        # Broadcast
        try:
            from core.hub import hub
            import asyncio
            if hub and hub._loop:
                asyncio.run_coroutine_threadsafe(
                    hub.broadcast({"type": "plan.created", "plan_id": plan["plan_id"],
                                   "title": plan["title"], "source": "autoload"}),
                    hub._loop,
                )
        except Exception:
            pass

        # Notification
        try:
            from core.database import _db_connection
            conn = _db_connection()
            with conn:
                conn.execute(
                    "INSERT INTO notifications (text, color, category, created_at, read) VALUES (?,?,?,?,0)",
                    (f"📋 Plan auto-imported: {plan['title']}", "#2d84ff", "plans", _now_iso())
                )
        except Exception:
            pass

        dest = PLAN_PROCESSED_DIR / f"{path.stem}__{digest[:8]}{path.suffix}"
        _move(path, dest)
        seen.add(digest)

        logger.info("plan_autoload: imported plan '%s' (%s) from %s", plan["title"], plan["plan_id"], fname)
        results.append({"file": fname, "status": "imported", "plan_id": plan["plan_id"], "error": None})

    _save_manifest(seen)
    return results


def _move(src: Path, dst: Path) -> None:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    except Exception as exc:
        logger.warning("plan_autoload: could not move %s → %s: %s", src, dst, exc)


async def async_scan_plan_inbox() -> list[dict]:
    """Async wrapper — runs scan_plan_inbox() in a thread pool executor."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, scan_plan_inbox)
