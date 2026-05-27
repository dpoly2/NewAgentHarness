"""
Local Adapter — bridges LangGraph state to SQLite + filesystem.
Used by the offline AgentHarness desktop tool.
"""
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

MEMORY_DIR  = Path(__file__).parent.parent / "memory"
SKILLS_DIR  = Path(__file__).parent.parent.parent / "skills"
DB_PATH     = MEMORY_DIR / "runs.db"
MEMORY_JSON = MEMORY_DIR / "agent_memory.json"
SKILLS_JSON = Path(__file__).parent.parent / "skills_db" / "skills_index.json"


def _ensure_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (Path(__file__).parent.parent / "skills_db").mkdir(parents=True, exist_ok=True)
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _get_db():
    _ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            agent_id TEXT,
            project TEXT,
            task TEXT,
            score REAL,
            critique TEXT,
            revision_count INTEGER,
            output_summary TEXT,
            skill_version INTEGER,
            status TEXT,
            environment TEXT DEFAULT 'local',
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            skill_name TEXT,
            version INTEGER,
            content TEXT,
            avg_score REAL,
            last_critique TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


class LocalAdapter:
    """Bridge for offline AgentHarness tool — SQLite + filesystem."""

    # ── Memory ────────────────────────────────────────────────────────────────

    def read_memory(self, agent_id: str) -> str:
        """Pull most recent run summary for this agent from SQLite."""
        try:
            conn = _get_db()
            row = conn.execute(
                "SELECT score, critique, skill_version, created_at "
                "FROM agent_runs WHERE agent_id=? AND status='complete' "
                "ORDER BY id DESC LIMIT 1",
                (agent_id,)
            ).fetchone()
            conn.close()
            if row:
                score, critique, version, ts = row
                return (
                    f"Last run ({ts[:10]}): score={score:.2f}, "
                    f"skill v{version}. Critique: {critique or 'none'}"
                )
        except Exception:
            pass

        # Fallback: check agent_memory.json
        if MEMORY_JSON.exists():
            try:
                mem = json.loads(MEMORY_JSON.read_text())
                if agent_id in mem:
                    return str(mem[agent_id])
            except Exception:
                pass
        return "No prior memory found."

    def write_memory(self, agent_id: str, run_id: str, score: float,
                     critique: str, output_summary: str,
                     task: str, project: str, revision_count: int,
                     skill_version: int, status: str = "complete") -> None:
        """Log completed run to SQLite."""
        try:
            conn = _get_db()
            conn.execute(
                "INSERT INTO agent_runs "
                "(run_id, agent_id, project, task, score, critique, "
                "revision_count, output_summary, skill_version, status, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, agent_id, project, task, round(score, 3), critique,
                 revision_count, output_summary[:500], skill_version, status,
                 datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LocalAdapter] write_memory error: {e}")

        # Also update agent_memory.json for quick reads
        _ensure_dirs()
        mem = {}
        if MEMORY_JSON.exists():
            try:
                mem = json.loads(MEMORY_JSON.read_text())
            except Exception:
                pass
        mem[agent_id] = {
            "last_run": run_id,
            "last_score": score,
            "last_critique": critique,
            "skill_version": skill_version,
            "updated_at": datetime.utcnow().isoformat(),
        }
        MEMORY_JSON.write_text(json.dumps(mem, indent=2))

    # ── Skills ────────────────────────────────────────────────────────────────

    def read_skill(self, skill_name: str) -> tuple[str, int]:
        """Return (content, version) for the current skill."""
        skill_file = SKILLS_DIR / f"{skill_name}.md"
        if skill_file.exists():
            content = skill_file.read_text()
            version = 1
            for line in content.splitlines()[:3]:
                if "v" in line and line.strip().startswith("#"):
                    try:
                        version = int(line.split("v")[-1].strip())
                    except ValueError:
                        pass
            return content, version
        return "", 1

    def write_skill(self, skill_name: str, content: str, version: int,
                    score: float, critique: str, agent_id: str) -> None:
        """Save updated skill to disk and log to SQLite + skills_index.json."""
        _ensure_dirs()
        skill_file = SKILLS_DIR / f"{skill_name}.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content)
        print(f"[LocalAdapter] Skill '{skill_name}' updated → v{version} (score:{score:.2f})")

        # Log to SQLite
        try:
            conn = _get_db()
            conn.execute(
                "INSERT INTO skill_versions "
                "(agent_id, skill_name, version, content, avg_score, last_critique, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (agent_id, skill_name, version, content[:2000],
                 round(score, 3), critique[:500],
                 datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LocalAdapter] write_skill db error: {e}")

        # Update skills_index.json
        idx_path = Path(__file__).parent.parent / "skills_db" / "skills_index.json"
        idx = {}
        if idx_path.exists():
            try:
                idx = json.loads(idx_path.read_text())
            except Exception:
                pass
        if agent_id not in idx:
            idx[agent_id] = {"current_version": 1, "avg_score": 0.0,
                             "total_runs": 0, "skill_file": str(skill_file), "history": []}
        idx[agent_id]["current_version"] = version
        idx[agent_id]["avg_score"] = score
        idx[agent_id]["total_runs"] += 1
        idx[agent_id]["history"].append({
            "version": version, "score": score,
            "critique": critique, "date": datetime.utcnow().date().isoformat()
        })
        idx_path.write_text(json.dumps(idx, indent=2))

    # ── Tools ─────────────────────────────────────────────────────────────────

    def run_tool(self, tool_name: str, args: dict) -> str:
        """Execute a local skill script."""
        for ext in ["js", "py", "sh"]:
            skill_file = SKILLS_DIR / f"{tool_name}.{ext}"
            if skill_file.exists():
                try:
                    cmd = {"js": ["node"], "py": ["python3"], "sh": ["bash"]}[ext]
                    result = subprocess.run(
                        cmd + [str(skill_file), json.dumps(args)],
                        capture_output=True, text=True, timeout=60
                    )
                    return result.stdout or result.stderr
                except Exception as e:
                    return f"Tool error: {e}"
        return f"Tool '{tool_name}' not found in skills directory."
