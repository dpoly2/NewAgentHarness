"""hub_backup.py — ArchonHub DB backup to JSON (git-tracked).

Exports critical tables (clients, agents, users, projects, todos, connectors,
scheduled_jobs) to .agents/data/backup/ so they survive DB wipes and are
versioned by git.

Usage:
  backup_clients()   — lightweight; called on every client write
  backup_all()       — full backup; called nightly by scheduler
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("hub_backup")

_REPO_ROOT = Path(__file__).resolve().parents[4]  # NewAgentHarness/
BACKUP_DIR = _REPO_ROOT / ".agents" / "data" / "backup"


def _ensure_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _write(filename: str, data: object) -> None:
    _ensure_dir()
    path = BACKUP_DIR / filename
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)
    logger.debug("Backup written: %s (%d records)", filename, len(data) if isinstance(data, list) else 1)  # type: ignore[arg-type]


def backup_clients() -> None:
    """Export clients table to clients.json. Called on every client mutation."""
    try:
        import hub_db
        clients = hub_db.list_clients()
        _write("clients.json", clients)
        logger.info("Client backup: %d clients saved to data/backup/clients.json", len(clients))
    except Exception:
        logger.exception("backup_clients() failed")


def backup_all() -> None:
    """Full export of all critical tables. Called nightly by scheduler."""
    try:
        import hub_db

        payload: dict[str, object] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "clients": hub_db.list_clients(),
            "agents": hub_db.list_agents(),
            "users": hub_db.list_users(),
            "projects": hub_db.list_projects(),
            "todos": hub_db.list_todos(),
            "connectors": hub_db.list_connectors(),
            "scheduled_jobs": hub_db.list_scheduled_jobs(),
            "skills": hub_db.list_skills(),
        }

        # Write full backup
        _write("archonhub_backup.json", payload)

        # Also keep clients.json in sync
        _write("clients.json", payload["clients"])

        counts = {k: len(v) for k, v in payload.items() if isinstance(v, list)}  # type: ignore[union-attr]
        logger.info("Full backup complete: %s", counts)
    except Exception:
        logger.exception("backup_all() failed")
