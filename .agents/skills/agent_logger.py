"""
AgentLogger — Base44-native reflexion logging skill.
Called at the END of any agent task run inside Base44.

Usage (in any agent task handler):
    from agent_logger import AgentLogger
    logger = AgentLogger()
    logger.log_run(
        agent_id="xftc-plugin-dev",
        project="xftc",
        task="Build leaderboard REST endpoint",
        output="<full output text>",
        score=0.88,
        critique="Good structure, missing error handling on empty results.",
        revision_count=1,
        skill_version=2,
        status="complete"   # or "partial" / "failed"
    )
    logger.update_skill(
        agent_id="xftc-plugin-dev",
        skill_name="xftc_plugin_dev",
        version=2,
        content="<updated skill markdown>",
        avg_score=0.88,
        critique="Good structure, missing error handling on empty results."
    )

Environment variables required:
    BASE44_API_KEY  — your Base44 API key
    BASE44_APP_ID   — app ID (default: 6a0bce17b730c0de488b80fb)
"""

import os
import json
import uuid
import requests
from datetime import datetime

BASE44_API = "https://api.base44.com"
APP_ID     = os.environ.get("BASE44_APP_ID", "6a0bce17b730c0de488b80fb")
API_KEY    = os.environ.get("BASE44_API_KEY", "")


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _url(entity: str) -> str:
    return f"{BASE44_API}/apps/{APP_ID}/entities/{entity}"


class AgentLogger:
    """
    Lightweight wrapper for logging agent reflexion data to Base44 entities.
    Works without LangGraph — call it directly from any agent task.
    """

    def log_run(
        self,
        agent_id: str,
        project: str,
        task: str,
        output: str,
        score: float,
        critique: str,
        revision_count: int = 0,
        skill_version: int = 1,
        status: str = "complete",
        run_id: str = None,
        environment: str = "base44",
    ) -> dict:
        """
        Write a completed agent run to AgentRunLog.
        Returns the created record or an error dict.
        """
        if not run_id:
            run_id = str(uuid.uuid4())[:8]

        payload = {
            "run_id": run_id,
            "agent_id": agent_id,
            "project": project,
            "task": task[:500],
            "score": round(float(score), 3),
            "critique": critique[:1000] if critique else "",
            "revision_count": revision_count,
            "output_summary": output[:500] if output else "",
            "environment": environment,
            "skill_version": skill_version,
            "status": status,
        }

        try:
            r = requests.post(_url("AgentRunLog"), headers=_headers(),
                              json=payload, timeout=15)
            result = r.json()
            if r.status_code in (200, 201):
                print(f"[AgentLogger] ✅ Run logged — {agent_id} | score:{score:.2f} | run:{run_id}")
                return result
            else:
                print(f"[AgentLogger] ❌ Log failed ({r.status_code}): {result}")
                return {"error": result}
        except Exception as e:
            print(f"[AgentLogger] ❌ Exception: {e}")
            return {"error": str(e)}

    def update_skill(
        self,
        agent_id: str,
        skill_name: str,
        version: int,
        content: str,
        avg_score: float,
        critique: str,
        total_runs: int = 1,
        environment: str = "base44",
    ) -> dict:
        """
        Write or update a skill version record in AgentSkillVersion.
        Call this every time a skill is revised (score < 0.75 triggers revision).
        """
        payload = {
            "agent_id": agent_id,
            "skill_name": skill_name,
            "version": version,
            "content": content[:2000] if content else "",
            "avg_score": round(float(avg_score), 3),
            "total_runs": total_runs,
            "last_critique": critique[:500] if critique else "",
            "environment": environment,
        }

        try:
            r = requests.post(_url("AgentSkillVersion"), headers=_headers(),
                              json=payload, timeout=15)
            result = r.json()
            if r.status_code in (200, 201):
                print(f"[AgentLogger] ✅ Skill v{version} logged — {skill_name} | avg_score:{avg_score:.2f}")
                return result
            else:
                print(f"[AgentLogger] ❌ Skill update failed ({r.status_code}): {result}")
                return {"error": result}
        except Exception as e:
            print(f"[AgentLogger] ❌ Exception: {e}")
            return {"error": str(e)}

    def get_agent_history(self, agent_id: str, limit: int = 10) -> list:
        """
        Pull the last N runs for a given agent from AgentRunLog.
        Useful for building memory context before a new run.
        """
        try:
            r = requests.get(
                _url("AgentRunLog"),
                headers=_headers(),
                params={"agent_id": agent_id, "limit": limit, "sort": "-created_date"},
                timeout=15,
            )
            data = r.json()
            return data.get("data", data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"[AgentLogger] ❌ get_agent_history error: {e}")
            return []

    def get_skill_version(self, agent_id: str) -> dict:
        """
        Get the latest skill version record for an agent.
        Returns dict with version, avg_score, last_critique, content.
        """
        try:
            r = requests.get(
                _url("AgentSkillVersion"),
                headers=_headers(),
                params={"agent_id": agent_id, "limit": 1, "sort": "-version"},
                timeout=15,
            )
            data = r.json()
            records = data.get("data", data) if isinstance(data, dict) else data
            return records[0] if records else {}
        except Exception as e:
            print(f"[AgentLogger] ❌ get_skill_version error: {e}")
            return {}


# ── Standalone evaluation helper ────────────────────────────────────────────

def evaluate_output(task: str, output: str, model: str = "gpt-4o") -> dict:
    """
    Score an agent output using the same 3-criteria rubric as the harness.
    Returns: {"completion": float, "quality": float, "efficiency": float,
              "overall": float, "critique": str}
    
    Requires OPENAI_API_KEY in env.
    """
    import os
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
    except ImportError:
        return {"overall": 0.0, "critique": "langchain_openai not installed"}

    SYSTEM = """You are a strict but fair quality evaluator for AI agent outputs.
Score on 3 criteria (0.0–1.0 each):
1. COMPLETION — Did the agent fully complete the task?
2. QUALITY    — Is the output accurate, well-structured, and useful?
3. EFFICIENCY — Is the output concise and free of unnecessary content?

Respond ONLY with valid JSON:
{
  "completion": 0.0,
  "quality": 0.0,
  "efficiency": 0.0,
  "overall": 0.0,
  "critique": "Specific, actionable feedback."
}
overall = completion*0.5 + quality*0.35 + efficiency*0.15"""

    try:
        llm = ChatOpenAI(model=model, temperature=0.0)
        response = llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"TASK:\n{task}\n\nOUTPUT:\n{output}\n\nScore this."),
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return {"overall": 0.0, "critique": f"Evaluation error: {e}"}


if __name__ == "__main__":
    # Quick smoke test
    print("AgentLogger — smoke test")
    logger = AgentLogger()
    result = logger.log_run(
        agent_id="test-agent",
        project="test",
        task="Verify AgentLogger is wired up correctly",
        output="AgentLogger initialized and connected to Base44 entities.",
        score=0.95,
        critique="No issues — baseline connectivity confirmed.",
        revision_count=0,
        skill_version=1,
        status="complete",
    )
    print("Result:", result)
