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
    except ValueError:
        # Re-raise config errors (missing API key etc.) — don't fall back silently
        raise
    except Exception:
        pass
    # Bare fallback — direct OpenAI (only reached if hub_nodes not importable)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "No API key configured. Go to Admin → AI Provider in ArchonHub and enter your API key."
        )
    return ChatOpenAI(model=MODEL, temperature=temperature, api_key=api_key)


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


# ── Travel tools ─────────────────────────────────────────────────────────────

import urllib.request as _urllib_req
import urllib.parse as _urllib_parse

_TRAVEL_PATTERNS = [
    r"(?:plan|create|add|book|start|set up)\s+(?:a\s+)?trip",
    r"trip\s+(?:from|to)\s+\w+",
    r"travel(?:l?ing)?\s+(?:from|to)\s+\w+",
    r"fly(?:ing)?\s+(?:from|to)\s+\w+",
    r"(?:going|headed|heading)\s+to\s+[A-Z]",
    r"hotels?\s+(?:in|near|at)\s+\w+",
    r"(?:find|search|look up)\s+hotels?",
]


def _is_travel_request(msg: str) -> bool:
    ml = msg.lower()
    return any(re.search(p, ml, re.IGNORECASE) for p in _TRAVEL_PATTERNS)


def _geocode(place: str) -> tuple[float, float] | None:
    """Geocode a place name to (lat, lon) via Nominatim (free, no key)."""
    try:
        url = "https://nominatim.openstreetmap.org/search?" + _urllib_parse.urlencode(
            {"q": place, "format": "json", "limit": 1}
        )
        req = _urllib_req.Request(url, headers={"User-Agent": "ArchonHub/1.0 (travel-research)"})
        with _urllib_req.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.debug("Geocode failed for %r: %s", place, e)
    return None


def _hotels_near(lat: float, lon: float, radius: int = 5000) -> list[dict]:
    """Query Overpass API for hotels within radius meters of lat/lon."""
    query = (
        f"[out:json][timeout:15];"
        f"("
        f"  node['tourism'='hotel'](around:{radius},{lat},{lon});"
        f"  way['tourism'='hotel'](around:{radius},{lat},{lon});"
        f"  node['tourism'='motel'](around:{radius},{lat},{lon});"
        f"  node['tourism'='guest_house'](around:{radius},{lat},{lon});"
        f");"
        f"out body;"
    )
    try:
        data = _urllib_parse.urlencode({"data": query}).encode()
        req = _urllib_req.Request(
            "https://overpass-api.de/api/interpreter",
            data=data,
            headers={"User-Agent": "ArchonHub/1.0"},
        )
        with _urllib_req.urlopen(req, timeout=16) as r:
            result = json.loads(r.read())
        hotels = []
        for el in result.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", "")
            if not name:
                continue
            stars_raw = tags.get("stars", "")
            stars = ("★" * int(stars_raw)) if stars_raw.isdigit() else ""
            hotels.append({
                "name": name,
                "stars": stars,
                "website": tags.get("website", tags.get("contact:website", "")),
                "phone": tags.get("phone", tags.get("contact:phone", "")),
                "address": " ".join(filter(None, [
                    tags.get("addr:housenumber", ""),
                    tags.get("addr:street", ""),
                    tags.get("addr:city", ""),
                ])),
            })
            if len(hotels) >= 12:
                break
        return hotels
    except Exception as e:
        logger.debug("Overpass hotel search failed: %s", e)
        return []


_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _extract_trip_info(msg: str) -> dict:
    """Extract source, destination, and dates from a natural-language message."""
    result = {"source": "", "destination": "", "depart_date": "", "return_date": "", "purpose": ""}

    # "from X to Y" pattern
    m = re.search(
        r"from\s+([A-Za-z][A-Za-z\s,]+?)\s+to\s+([A-Za-z][A-Za-z\s,]+?)(?=\s+(?:on|in|june|july|aug|jan|feb|mar|apr|may|sep|oct|nov|dec|\d{4})|[,.]|$)",
        msg, re.IGNORECASE
    )
    if m:
        result["source"] = m.group(1).strip().rstrip(",")
        result["destination"] = m.group(2).strip().rstrip(",")
    else:
        # "trip/travel/fly to X"
        m2 = re.search(
            r"(?:trip|travel|fly|going|headed|heading)\s+to\s+([A-Za-z][A-Za-z\s,]+?)(?=\s+(?:on|in|june|july|\d{4})|[,.]|$)",
            msg, re.IGNORECASE
        )
        if m2:
            result["destination"] = m2.group(1).strip().rstrip(",")

    # "June 20-25, 2026" or "Jun 20 – 25 2026"
    range_m = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
        r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+(\d{1,2})\s*[–—\-]\s*(\d{1,2}),?\s*(\d{4})",
        msg, re.IGNORECASE
    )
    if range_m:
        month = _MONTH_MAP.get(range_m.group(1).lower()[:3], "01")
        year = range_m.group(4)
        result["depart_date"] = f"{year}-{month}-{range_m.group(2).zfill(2)}"
        result["return_date"]  = f"{year}-{month}-{range_m.group(3).zfill(2)}"
    else:
        # "June 20, 2026" single date → depart only
        single_m = re.search(
            r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
            r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"\s+(\d{1,2}),?\s*(\d{4})",
            msg, re.IGNORECASE
        )
        if single_m:
            month = _MONTH_MAP.get(single_m.group(1).lower()[:3], "01")
            result["depart_date"] = f"{single_m.group(3)}-{month}-{single_m.group(2).zfill(2)}"

    # ISO date fallback "2026-06-20"
    if not result["depart_date"]:
        iso_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", msg)
        if iso_dates:
            result["depart_date"] = iso_dates[0]
            if len(iso_dates) > 1:
                result["return_date"] = iso_dates[1]

    return result


def _handle_trip_creation(user_message: str) -> str:
    """
    Core travel tool: extract trip params, create DB record, geocode destination,
    search nearby hotels. Returns a context block injected into the LLM prompt.
    """
    if not DB_OK:
        return ""

    info = _extract_trip_info(user_message)
    dest = info.get("destination", "").strip()
    if not dest:
        return ""

    source = info.get("source", "").strip() or "Austin, TX"
    trip_name = f"{source} \u2192 {dest}"

    # Create the trip in DB (idempotent by name)
    trip_created = False
    try:
        existing_names = {t.get("name", "") for t in db.list_trips()}
        if trip_name not in existing_names:
            db.create_trip(
                name=trip_name,
                destination=dest,
                depart_date=info.get("depart_date", ""),
                return_date=info.get("return_date", ""),
                status="planning",
                notes=f"Created by Inez. Purpose: {info.get('purpose') or 'TBD'}",
            )
            trip_created = True
    except Exception as e:
        logger.warning("Trip DB create failed: %s", e)

    # Geocode + hotel search
    hotel_lines: list[str] = []
    coords = _geocode(dest)
    if coords:
        lat, lon = coords
        hotels = _hotels_near(lat, lon)
        if hotels:
            hotel_lines.append(f"HOTELS NEAR {dest.upper()} (OpenStreetMap data, sorted by proximity):")
            for h in hotels:
                parts = [f"  • {h['name']}"]
                if h.get("stars"):
                    parts[0] += f" {h['stars']}"
                if h.get("address"):
                    parts[0] += f" — {h['address']}"
                if h.get("website"):
                    parts[0] += f" | {h['website']}"
                if h.get("phone"):
                    parts[0] += f" | {h['phone']}"
                hotel_lines.append(parts[0])
        else:
            hotel_lines.append(
                f"No hotels found via Overpass within 5km of {dest}. "
                "Recommend searching Booking.com, Hotels.com, or Google Hotels."
            )
    else:
        hotel_lines.append(
            f"Could not geocode '{dest}'. Provide a more specific city/address for hotel search."
        )

    action = "created" if trip_created else "already exists"
    return (
        f"[TRIP TOOL RESULT]\n"
        f"Trip '{trip_name}' {action} in Travel tab.\n"
        f"Departure: {info.get('depart_date') or 'TBD'}  |  Return: {info.get('return_date') or 'TBD'}\n"
        f"Status: planning\n\n"
        + "\n".join(hotel_lines)
    )


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

    travel_tools_note = (
        "\n\nTRAVEL TOOLS: When the user asks to plan/create a trip or find hotels, "
        "a pre-execution tool has already geocoded the destination and searched for nearby hotels via OpenStreetMap. "
        "The results will appear in [TOOL RESULTS] in the user message. "
        "Present the hotel list clearly, note which ones have websites/phone numbers, "
        "and confirm the trip has been saved to the Travel tab."
    )

    base = (
        skill
        .replace("{todos_context}", todos)
        .replace("{memory_context}", full_memory)
        .replace("{conversation_history}", conv)
    )
    return base + travel_tools_note


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

    Flow:
      1. Inez analyzes request → produces inez_message + dispatches list
      2. Each dispatch runs through agent_runner.run_agent() (skill + LLM + DB writes)
      3. Agent results are synthesized: Inez calls LLM again with all agent outputs
      4. Final synthesized response returned to user

    Returns:
        {
            "inez_message": str,         # Inez's final synthesized response
            "dispatches": list[dict],    # Agents that were dispatched
            "agent_results": list[dict], # Raw results from each agent
            "needs_agents": bool,
            "todos": list[dict],
            "tasks": list[dict],
            "error": str | None,
        }
    """
    if not LLM_OK:
        return {
            "inez_message": INEZ_FALLBACK,
            "dispatches": [],
            "agent_results": [],
            "needs_agents": False,
            "todos": [],
            "tasks": [],
            "error": "LangChain/OpenAI not installed",
        }

    if emit:
        emit("inez_thinking", message="Inez is analyzing your request...")

    # ── Step 1: Travel pre-fetch (geocode + hotel data → passed as context to agent) ──
    travel_tool_data = ""
    if _is_travel_request(user_message):
        try:
            trip_info = _extract_trip_info(user_message)
            dest = trip_info.get("destination", "")
            if dest:
                if emit:
                    emit("inez_thinking", message=f"Looking up hotels near {dest}...")
                coords = _geocode(dest)
                if coords:
                    hotels = _hotels_near(*coords)
                    if hotels:
                        lines = [f"Hotels near {dest} (OpenStreetMap):"]
                        for h in hotels:
                            parts = [f"  • {h['name']}"]
                            if h.get("stars"):
                                parts[0] += f" {h['stars']}"
                            if h.get("address"):
                                parts[0] += f" — {h['address']}"
                            if h.get("website"):
                                parts[0] += f" | {h['website']}"
                            lines.append(parts[0])
                        travel_tool_data = "\n".join(lines)
        except Exception as _te:
            logger.warning("Travel pre-fetch error: %s", _te)

    system_prompt = _build_system_prompt(history)

    # ── Step 2: Inez analysis — determines what to say and who to dispatch ────
    dispatch_instructions = (
        "\n\nDISPATCH INSTRUCTIONS: When you need agents to do work, include a JSON block:\n"
        "```json\n"
        '{"inez_message": "...", "dispatches": [{"agent_id": "agent-id", "task": "specific task description", '
        '"project": "project-slug", "context": "any extra context the agent needs"}]}\n'
        "```\n"
        "For travel requests, dispatch to: travel-project-lead (orchestrator), "
        "travel-hotel-agent (lodging), travel-flights-agent (flights), travel-budget-helper (budget).\n"
        "For project work, dispatch the relevant specialist agent.\n"
        "Agents will execute the task, write results to the database, and report back."
    )

    augmented_message = user_message
    if travel_tool_data:
        augmented_message = (
            f"{user_message}\n\n"
            f"[PRE-FETCHED TOOL DATA — pass this to the travel agent as context]:\n"
            f"{travel_tool_data}"
        )

    try:
        model = _llm(temperature=0.3)
        messages = [
            SystemMessage(content=system_prompt + dispatch_instructions),
            HumanMessage(content=augmented_message),
        ]
        response = model.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        result = _parse_inez_response(raw)
        result["error"] = None
        result.setdefault("agent_results", [])

        # ── Step 3: Execute dispatches through agent_runner ───────────────────
        dispatches = result.get("dispatches", [])
        if dispatches:
            if emit:
                emit("inez_thinking", message=f"Dispatching {len(dispatches)} agent(s)...")
            try:
                from agent_runner import run_dispatches, build_synthesis_context
                # Inject travel tool data as context for travel agents
                for d in dispatches:
                    if travel_tool_data and "travel" in d.get("agent_id", "").lower():
                        d["context"] = (d.get("context", "") + "\n\n" + travel_tool_data).strip()
                agent_results = run_dispatches(dispatches, emit=emit)
                result["agent_results"] = agent_results

                # ── Step 4: Synthesis — Inez reads all agent outputs ──────────
                synthesis_context = build_synthesis_context(agent_results)
                if synthesis_context:
                    if emit:
                        emit("inez_thinking", message="Synthesizing agent results...")
                    synth_messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=(
                            f"Original request: {user_message}\n\n"
                            f"{synthesis_context}\n\n"
                            "Now provide your final synthesized response to the user. "
                            "Be concise and actionable. Reference what was saved to the database."
                        )),
                    ]
                    synth_response = model.invoke(synth_messages)
                    synth_raw = synth_response.content if hasattr(synth_response, "content") else str(synth_response)
                    # Use synthesis as final message, keep original as fallback
                    synth_parsed = _parse_inez_response(synth_raw)
                    if synth_parsed.get("inez_message"):
                        result["inez_message"] = synth_parsed["inez_message"]
            except ImportError:
                logger.warning("agent_runner not available — dispatches not executed")
            except Exception as de:
                logger.error("Dispatch execution error: %s", de)

        # ── Persist todos Inez created directly ──────────────────────────────
        if DB_OK and result.get("todos"):
            for todo in result["todos"]:
                try:
                    db.create_todo(
                        title=todo.get("title", ""),
                        description=todo.get("description", ""),
                        priority=todo.get("priority", "medium"),
                        project=todo.get("projectSlug", todo.get("project", "")),
                        due_date=todo.get("dueDate"),
                        tags=todo.get("tags", []),
                        source="inez",
                    )
                except Exception:
                    pass

        # ── Save exchange to Inez's memory ────────────────────────────────────
        if DB_OK:
            try:
                db.save_memory(
                    INEZ_AGENT_ID,
                    f"exchange_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    json.dumps({
                        "user":       user_message[:200],
                        "inez":       result["inez_message"][:200],
                        "agents":     [r.get("agent_id") for r in result.get("agent_results", [])],
                        "db_writes":  sum(r.get("db_writes_applied", 0) for r in result.get("agent_results", [])),
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
            "inez_message":  msg,
            "dispatches":    [],
            "agent_results": [],
            "needs_agents":  False,
            "todos":         [],
            "tasks":         [],
            "error":         err_str,
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
