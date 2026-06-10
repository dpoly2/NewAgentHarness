"""
inez_agent.py — Inez, Chief of Staff
=====================================
Inez is the primary interface for the ArchonHub portfolio.
She is the successor to AgentMajesty — all prior memory, protocols,
and conversation history carry forward under the new identity.

She analyzes requests, determines which agents to deploy,
dispatches tasks, creates todos, generates morning briefs,
and synthesizes results.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
SKILL_PATH = AGENTS_DIR / "agents" / "projects" / "inez" / "inez-chief-of-staff.md"
S2T_ROSTER_PATH = AGENTS_DIR / "projects" / "s2tdesigns" / "CLIENT-ROSTER.md"
S2T_CLIENTS_DIR = AGENTS_DIR / "projects" / "s2tdesigns" / "clients"

# Legacy agent IDs — memory is read from both
LEGACY_AGENT_ID = "agentmajesty"
INEZ_AGENT_ID = "inez-chief-of-staff"

# ── LLM setup ────────────────────────────────────────────────────────────────
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LLM_OK = True
except ImportError:
    LLM_OK = False

try:
    import hub_db as db
    DB_OK = True
except ImportError:
    DB_OK = False

try:
    from ah_logging import get_logger
    logger = get_logger("inez")
except Exception:
    import logging
    logger = logging.getLogger("inez")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

INEZ_FALLBACK = (
    "I'm Inez, Chief of Staff. I'm currently unable to connect to the AI engine. "
    "Please go to Admin → AI Provider, set your provider and API key, then save."
)


def _llm(temperature: float = 0.3):
    """Use the shared multi-provider LLM factory from hub_nodes when available."""
    try:
        from hub_nodes import _llm as _hub_llm
        return _hub_llm(temperature=temperature)
    except Exception:
        pass
    # Bare fallback — direct OpenAI
    return ChatOpenAI(
        model=MODEL,
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    )


def _load_skill() -> str:
    """Load Inez's skill/system prompt from disk."""
    try:
        return SKILL_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Inez, Chief of Staff for the Smith Capital Portfolio."


def _load_client_roster() -> str:
    """Load S2T Designs client roster and scan client folders for PROJECT.md status."""
    lines = []
    try:
        roster_text = S2T_ROSTER_PATH.read_text(encoding="utf-8")
        table_match = re.search(r"## Active Clients[\s\S]*?\n((?:\|[^\n]+\n)+)", roster_text)
        if table_match:
            lines.append("S2T DESIGNS ACTIVE CLIENTS:")
            rows = table_match.group(1).strip().split("\n")[2:]  # skip header + separator
            for row in rows:
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if len(cells) >= 3:
                    lines.append(f"  • {cells[0]} — {cells[-1]}")
    except Exception:
        pass

    try:
        if S2T_CLIENTS_DIR.exists():
            for client_dir in sorted(S2T_CLIENTS_DIR.iterdir()):
                if not client_dir.is_dir():
                    continue
                proj_file = client_dir / "PROJECT.md"
                if not proj_file.exists():
                    continue
                text = proj_file.read_text(encoding="utf-8")
                name_match = re.search(r"^# (.+)", text, re.MULTILINE)
                status_match = re.search(r"(?:Current Status|Status)[:\s]+(.+)", text, re.IGNORECASE)
                blockers = re.findall(r"- \[ \] (.+)", text)[:2]
                name = name_match.group(1) if name_match else client_dir.name.upper()
                status = f" — {status_match.group(1).strip()}" if status_match else ""
                blocker_str = f"\n      Blockers: {'; '.join(blockers)}" if blockers else ""
                lines.append(f"  [{client_dir.name.upper()}] {name}{status}{blocker_str}")
    except Exception:
        pass

    return "\n".join(lines) if lines else ""


def _load_portfolio_context() -> str:
    """Load full portfolio context from DB — projects, clients, agents, automations."""
    if not DB_OK:
        return ""
    lines = []
    try:
        # Projects
        projects = db.list_projects()
        if projects:
            lines.append("ACTIVE PROJECTS:")
            for p in projects:
                status = p.get("status", "")
                lead = p.get("lead_agent", "")
                url = p.get("url", "")
                url_str = f" [{url}]" if url else ""
                lines.append(f"  • {p.get('name','')} ({p.get('slug','')}) — {status} | Lead: {lead}{url_str}")
    except Exception:
        pass

    try:
        # Clients
        clients = db.list_clients()
        if clients:
            lines.append("\nCLIENTS:")
            for c in clients:
                lines.append(
                    f"  • {c.get('name','')} ({c.get('slug','')}) — {c.get('status','')} | "
                    f"Contact: {c.get('contact_name','')} | {c.get('notes','')[:120]}"
                )
    except Exception:
        pass

    try:
        # Active agents summary
        agents = [a for a in db.list_agents() if a.get("status") == "active"]
        if agents:
            lines.append(f"\nAGENTS: {len(agents)} active agents across {len(set(a.get('project_slug','') for a in agents))} projects")
    except Exception:
        pass

    try:
        # Automations
        autos = db.list_automations(status="active")
        if autos:
            lines.append("\nACTIVE AUTOMATIONS:")
            for a in autos[:10]:
                lines.append(f"  • {a.get('name','')} ({a.get('trigger_type','manual')}) — {a.get('project_slug','')}")
    except Exception:
        pass

    return "\n".join(lines) if lines else ""


def _load_client_roster() -> str:
    """Load S2T Designs client roster — first tries DB, falls back to file scan."""
    # Try DB first
    if DB_OK:
        try:
            clients = db.list_clients()
            if clients:
                lines = ["S2T / PORTFOLIO CLIENTS:"]
                for c in clients:
                    lines.append(f"  • {c.get('name','')} — {c.get('status','')} | {c.get('notes','')[:100]}")
                return "\n".join(lines)
        except Exception:
            pass

    # Fallback: file scan
    lines = []
    try:
        roster_text = S2T_ROSTER_PATH.read_text(encoding="utf-8")
        table_match = re.search(r"## Active Clients[\s\S]*?\n((?:\|[^\n]+\n)+)", roster_text)
        if table_match:
            lines.append("S2T DESIGNS ACTIVE CLIENTS:")
            rows = table_match.group(1).strip().split("\n")[2:]
            for row in rows:
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if len(cells) >= 3:
                    lines.append(f"  • {cells[0]} — {cells[-1]}")
    except Exception:
        pass
    return "\n".join(lines) if lines else ""


def _load_todos_context() -> str:
    """Load current todos as context for Inez."""
    if not DB_OK:
        return "No todos available."
    try:
        todos = db.list_todos(status="pending") + db.list_todos(status="in_progress")
        if not todos:
            return "No active todos."
        lines = ["Active Todos:"]
        for t in todos[:20]:
            due = f" (due {t.get('due_date')})" if t.get("due_date") else ""
            agent = f" → {t.get('assigned_agent')}" if t.get("assigned_agent") else ""
            lines.append(
                f"- [{t.get('priority','med').upper()}] {t.get('title','')} "
                f"| {t.get('project','')} | {t.get('status','')}{due}{agent}"
            )
        return "\n".join(lines)
    except Exception:
        return "Todos unavailable."


def _load_memory_context() -> str:
    """Load Inez's memory — reads both inez and legacy agentmajesty keys."""
    if not DB_OK:
        return ""
    lines = []
    for agent_id in (INEZ_AGENT_ID, LEGACY_AGENT_ID):
        try:
            ctx = db.load_memory_context(agent_id)
            if ctx:
                lines.append(ctx)
        except Exception:
            pass
    return "\n".join(lines) if lines else ""


def _format_conversation_history(history: list[dict]) -> str:
    """Format prior conversation turns for context."""
    if not history:
        return "No prior conversation."
    lines = []
    for turn in history[-10:]:
        role = "You (Inez)" if turn.get("role") in ("inez", "assistant") else "David"
        lines.append(f"{role}: {turn.get('content', '')[:300]}")
    return "\n".join(lines)


def _build_system_prompt(history: list[dict]) -> str:
    """Build Inez's full system prompt with live context injected from DB."""
    skill = _load_skill()
    todos = _load_todos_context()
    memory = _load_memory_context()
    conv = _format_conversation_history(history)

    # Pull full portfolio context from DB (replaces file-based client roster)
    portfolio = _load_portfolio_context()
    client_roster = _load_client_roster() if not portfolio else ""

    full_memory = "\n\n".join(filter(None, [portfolio, client_roster, memory])) or "No prior memory."

    return (
        skill
        .replace("{todos_context}", todos)
        .replace("{memory_context}", full_memory)
        .replace("{conversation_history}", conv)
    )


def _parse_inez_response(raw: str) -> dict:
    """
    Extract structured response from Inez.
    Handles: JSON dispatch block, [TASK:] markers, [TODO:] markers.
    Falls back gracefully if JSON is missing or malformed.
    """
    result = {
        "inez_message": "",
        "dispatches": [],
        "needs_agents": False,
        "todos": [],
        "tasks": [],
    }

    # Extract [TODO:] markers
    todo_re = re.compile(r"\[TODO:\{([\s\S]*?)\}\]")
    for m in todo_re.finditer(raw):
        try:
            parsed = json.loads("{" + m.group(1) + "}")
            if parsed.get("title"):
                result["todos"].append(parsed)
        except Exception:
            pass

    # Extract [TASK:] markers (AgentMajesty compat)
    task_re = re.compile(r"\[TASK:\{([\s\S]*?)\}\]")
    for m in task_re.finditer(raw):
        try:
            parsed = json.loads("{" + m.group(1) + "}")
            if parsed.get("title"):
                result["tasks"].append(parsed)
        except Exception:
            pass

    # Strip markers from raw for further parsing
    clean = todo_re.sub("", raw)
    clean = task_re.sub("", clean).strip()

    # Try to find JSON dispatch block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
    if not json_match:
        json_match = re.search(r"(\{[^{}]*\"inez_message\"[^{}]*\})", clean, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if "inez_message" in data:
                result["inez_message"] = data["inez_message"]
                result["dispatches"] = data.get("dispatches", [])
                result["needs_agents"] = bool(result["dispatches"])
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: treat entire clean response as inez_message
    result["inez_message"] = clean
    return result


def think(
    user_message: str,
    history: list[dict],
    emit=None,
) -> dict:
    """
    Inez analyzes the user message and returns a structured response.

    Returns:
        {
            "inez_message": str,         # What Inez says to the user
            "dispatches": list[dict],    # Agents to deploy
            "needs_agents": bool,
            "todos": list[dict],         # Todos to create
            "tasks": list[dict],         # Tasks to enqueue (v2 compat)
            "error": str | None,
        }
    """
    if not LLM_OK:
        return {
            "inez_message": INEZ_FALLBACK,
            "dispatches": [],
            "needs_agents": False,
            "todos": [],
            "tasks": [],
            "error": "LangChain/OpenAI not installed",
        }

    if emit:
        emit("inez_thinking", message="Inez is analyzing your request...")

    system_prompt = _build_system_prompt(history)

    try:
        model = _llm(temperature=0.3)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        response = model.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        result = _parse_inez_response(raw)
        result["error"] = None

        # Persist todos to DB
        if DB_OK and result.get("todos"):
            for todo in result["todos"]:
                try:
                    db.create_todo(
                        title=todo.get("title", ""),
                        description=todo.get("description", ""),
                        priority=todo.get("priority", "medium"),
                        project=todo.get("projectSlug", ""),
                        due_date=todo.get("dueDate"),
                        tags=todo.get("tags", []),
                        source="inez",
                    )
                except Exception:
                    pass

        # Save exchange to Inez's memory
        if DB_OK:
            try:
                db.save_memory(
                    INEZ_AGENT_ID,
                    f"exchange_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    json.dumps({
                        "user": user_message[:200],
                        "inez": result["inez_message"][:200],
                    }),
                )
            except Exception:
                pass

        if emit:
            emit("inez_response",
                 message=result["inez_message"],
                 dispatches=result.get("dispatches", []))

        return result

    except Exception as exc:
        err_str = str(exc)
        logger.error("Inez LLM error: %s", exc)
        # Give a friendly message for common config errors
        if "api_key" in err_str.lower() or "credentials" in err_str.lower() or "OPENAI_API_KEY" in err_str:
            msg = (
                f"{INEZ_FALLBACK}\n\n"
                "Go to **Admin → AI Provider**, set your provider (e.g. OpenAI or Ollama) "
                "and enter your API key, then click Save."
            )
        elif "connection" in err_str.lower() or "refused" in err_str.lower() or "11434" in err_str:
            msg = (
                "I can't reach the Ollama server at localhost:11434. "
                "Please make sure Ollama is running (`ollama serve`) or switch to OpenAI in Admin → AI Provider."
            )
        else:
            msg = f"I ran into a problem: {err_str[:200]}"
        return {
            "inez_message": msg,
            "dispatches": [],
            "needs_agents": False,
            "todos": [],
            "tasks": [],
            "error": err_str,
        }


def generate_morning_brief(history: list[dict] = None) -> dict:
    """
    Generate a morning briefing for David.
    Returns {"content": str, "error": str|None}
    """
    if not LLM_OK:
        return {"content": INEZ_FALLBACK, "error": "LLM not available"}

    system_prompt = _build_system_prompt(history or [])
    brief_request = (
        "Generate my morning briefing. Include:\n"
        "1. One-sentence executive summary\n"
        "2. What needs my immediate attention (max 3 items)\n"
        "3. What agents are working on\n"
        "4. Key items this week\n\n"
        "Be direct and specific. Format as clean markdown."
    )

    try:
        model = _llm(temperature=0.2)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=brief_request),
        ]
        response = model.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        return {"content": content, "error": None}
    except Exception as exc:
        return {"content": f"Unable to generate briefing: {exc}", "error": str(exc)}


def save_memory(key: str, value: str) -> None:
    """Save a key/value to Inez's memory (also writable by legacy agentmajesty callers)."""
    if not DB_OK:
        return
    try:
        db.save_memory(INEZ_AGENT_ID, key, value)
    except Exception as exc:
        logger.warning("Memory save failed: %s", exc)


def think_async(
    user_message: str,
    history: list[dict],
    on_result,
    emit=None,
):
    """
    Run think() in a background thread.
    Calls on_result(result_dict) when complete.
    """
    def _run():
        result = think(user_message, history, emit=emit)
        on_result(result)

    t = threading.Thread(target=_run, daemon=True, name="InezThink")
    t.start()
    return t
