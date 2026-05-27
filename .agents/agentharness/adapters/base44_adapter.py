"""
Base44 Adapter — bridges LangGraph state to Base44 entities + skills.
Reads/writes AgentSkillVersion and AgentRunLog via Base44 REST API.
"""
import os
import json
import uuid
import requests
from datetime import datetime
from pathlib import Path

BASE44_API = os.environ.get("BASE44_API_URL", "https://api.base44.com")
APP_ID     = os.environ.get("BASE44_APP_ID", "6a0bce17b730c0de488b80fb")
API_KEY    = os.environ.get("BASE44_API_KEY", "")
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


def _headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def _entity_url(entity: str) -> str:
    return f"{BASE44_API}/apps/{APP_ID}/entities/{entity}"


class Base44Adapter:
    """Bridge between LangGraph AgentState and Base44 platform."""

    # ── Memory ────────────────────────────────────────────────────────────────

    def read_memory(self, agent_id: str) -> str:
        """Pull the most recent skill content + critique for this agent."""
        try:
            r = requests.get(
                _entity_url("AgentSkillVersion"),
                headers=_headers(),
                params={"agent_id": agent_id, "limit": 1, "sort": "-version"},
                timeout=15,
            )
            records = r.json().get("data", [])
            if records:
                rec = records[0]
                return (
                    f"Previous skill (v{rec.get('version', 1)}) "
                    f"scored {rec.get('avg_score', 0):.2f}. "
                    f"Last critique: {rec.get('last_critique', 'none')}"
                )
        except Exception:
            pass
        return "No prior memory found."

    def write_memory(self, agent_id: str, run_id: str, score: float,
                     critique: str, output_summary: str,
                     task: str, project: str, revision_count: int,
                     skill_version: int, status: str = "complete") -> None:
        """Log a completed run to AgentRunLog entity."""
        try:
            requests.post(
                _entity_url("AgentRunLog"),
                headers=_headers(),
                json={
                    "run_id": run_id,
                    "agent_id": agent_id,
                    "project": project,
                    "task": task,
                    "score": round(score, 3),
                    "critique": critique,
                    "revision_count": revision_count,
                    "output_summary": output_summary[:500],
                    "environment": "base44",
                    "skill_version": skill_version,
                    "status": status,
                },
                timeout=15,
            )
        except Exception as e:
            print(f"[Base44Adapter] write_memory error: {e}")

    # ── Skills ────────────────────────────────────────────────────────────────

    def read_skill(self, skill_name: str) -> tuple[str, int]:
        """Return (content, version) for the current skill."""
        skill_file = SKILLS_DIR / f"{skill_name}.md"
        if skill_file.exists():
            content = skill_file.read_text()
            # Parse version from first line: # Skill: name v3
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
        """Save updated skill to disk and log version to Base44."""
        skill_file = SKILLS_DIR / f"{skill_name}.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content)
        print(f"[Base44Adapter] Skill '{skill_name}' updated → v{version} (score:{score:.2f})")

        # Log to AgentSkillVersion entity
        try:
            requests.post(
                _entity_url("AgentSkillVersion"),
                headers=_headers(),
                json={
                    "agent_id": agent_id,
                    "skill_name": skill_name,
                    "version": version,
                    "content": content[:2000],  # truncate for storage
                    "avg_score": round(score, 3),
                    "total_runs": 1,
                    "last_critique": critique[:500],
                    "environment": "base44",
                },
                timeout=15,
            )
        except Exception as e:
            print(f"[Base44Adapter] write_skill entity error: {e}")

    # ── Tools ─────────────────────────────────────────────────────────────────

    def run_tool(self, tool_name: str, args: dict) -> str:
        """Execute a Base44 skill or backend function by name."""
        import subprocess
        skill_file = SKILLS_DIR / f"{tool_name}.js"
        if skill_file.exists():
            try:
                result = subprocess.run(
                    ["node", str(skill_file), json.dumps(args)],
                    capture_output=True, text=True, timeout=60
                )
                return result.stdout or result.stderr
            except Exception as e:
                return f"Tool error: {e}"
        return f"Tool '{tool_name}' not found."
