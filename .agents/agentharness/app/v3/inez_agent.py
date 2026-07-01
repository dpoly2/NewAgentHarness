"""
inez_agent.py — Inez, Chief of Staff
=====================================
Inez is the primary interface for the ArchonHub portfolio.
She is the successor to AgentMajesty — all prior memory, protocols,
and conversation history carry forward under the new identity.

She analyzes requests, determines which agents to deploy,
dispatches tasks, creates todos, generates morning briefs,
and synthesizes results.

Memory management:
  Exchange history is capped at 50 entries per agent (exchange_* keys). Older
  entries are pruned after each save to prevent unbounded agent_memory growth.

System prompt caching:
  _PROMPT_CACHE_TTL = 10.0 seconds. Prompts are cached per conversation_id[:16].
  Context changes (new todos, projects) are reflected within 10 seconds.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time as _time
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

try:
    from web_search import SerpAPIClient, SearchAnalyzer, CitationFormatter
    WEB_SEARCH_OK = True
except ImportError:
    WEB_SEARCH_OK = False
    logger.warning("web_search module not available — web search disabled")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# ── David's Identity Profile — injected into every Inez prompt ───────────────
DAVID_PROFILE = """
OPERATOR IDENTITY PROFILE — David Smith
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Roles:
  • HP Engineering Leader — Senior Network Engineer, Hewlett Packard Enterprise (primary income)
  • Founder & Director — Smith Capital Portfolio (holding company, all ventures)
  • Minister / Preacher — faith-based content, sermons, community leadership
  • Creative Director — Night King brand (media, design, production)
  • Head Coach / Athletic Director — XFTC (youth track club, WordPress + mobile app)

Communication Style:
  • Executive summary first — expand only when asked
  • Strategic recommendations required — not just information
  • Flag conflicts, risks, and deadlines proactively
  • No preamble — get to the point in 10 seconds of spoken content
  • Analyze → Recommend → Execute

Current Missions (Priority Order):
  1. ArchonHub — AI operating system, central intelligence build-out
  2. HP Engineering — daily work, primary income source
  3. XFTC — youth athletics, WordPress plugin + mobile app
  4. S2T Designs — web/digital agency, 5 active clients
  5. PBS Foundation — nonprofit, events + ticket fundraising
  6. Ministry — sermon writing, faith content
  7. SmithCap Finance — CFO, bookkeeping, portfolio finance
  8. Markets — investment intelligence, options strategy
  9. Nutrue Apparel — e-commerce brand build
  10. Sigma Signal — newsletter + media publication

Agent Command Network (Inez's team — code names David may use):
  Atlas    → Research & Intelligence (grants-research-agent, markets-intelligence-desk)
  Athena   → Strategy & Planning (markets-cio, finance-cfo)
  Forge    → Development (xftc-plugin-dev, s2t-webdev-agent, xftc-frontend-dev)
  Ledger   → Finance (finance-cfo, finance-bookkeeper, finance-tax-strategist)
  Guardian → Legal & Compliance (business-law-project-lead, holdings-legal-agent)
  Creator  → Design & Brand (nightking-design-agent, nutrue-brand-agent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

INEZ_FALLBACK = (
    "I'm Inez, Chief of Staff. I'm currently unable to connect to the AI engine. "
    "Please go to Admin → AI Provider, set your provider and API key, then save."
)

_PROMPT_CACHE: dict[str, tuple[str, float]] = {}
_PROMPT_CACHE_TTL = 10.0


def _llm(temperature: float = 0.3, weight: str = "light"):
    """Use the shared multi-provider LLM factory from hub_nodes when available.

    weight is forwarded to the factory: "heavy" prefers a fast free provider
    (round-robin balanced) over slow local Ollama for costly reasoning calls.
    """
    # Prefer a capable cloud model for Inez when an OpenAI key is configured.
    # Inez is the interactive assistant; with the free-proxy keys dead the only
    # other option is the slow local Ollama model, which makes chats hang on
    # "Consulting…". A working OpenAI key keeps Inez fast and reliable — scoped
    # to Inez only (background agents keep their existing routing). Model via
    # INEZ_MODEL; disable by clearing llm_key_openai.
    try:
        key = ""
        if DB_OK and hasattr(db, "get_config"):
            key = db.get_config("llm_key_openai") or ""
        key = key or os.environ.get("OPENAI_API_KEY", "")
        if key and str(key).startswith("sk-"):
            from llm_router import build_llm
            return build_llm(
                provider="openai",
                model=os.environ.get("INEZ_MODEL", "gpt-4o-mini"),
                api_key=key,
                temperature=temperature,
            )
    except Exception:
        pass
    try:
        from hub_nodes import _llm as _hub_llm
        return _hub_llm(temperature=temperature, weight=weight)
    except Exception:
        pass
    # Bare fallback — direct OpenAI
    return ChatOpenAI(
        model=MODEL,
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    )


def _is_slow_local_provider() -> bool:
    """True when chat will run on a slow local backend (Ollama) with no fast path.

    Used to skip optional secondary LLM calls (e.g. follow-up suggestions) that,
    stacked after the main analysis call on CPU-only hardware, can push a chat
    request past the reverse-proxy limit (~100s) and surface as a 524.

    Returns False when usable free providers exist — heavy calls then route to a
    fast remote key, so the secondary call is affordable again.
    """
    try:
        if DB_OK and hasattr(db, "get_config"):
            if (db.get_config("llm_provider") or "").lower() != "ollama":
                return False
            # Ollama configured, but a usable free provider makes heavy calls fast.
            try:
                from free_llm_keys import get_usable_free_providers
                if get_usable_free_providers():
                    return False
            except Exception:
                pass
            return True
    except Exception:
        pass
    return False


def _load_skill() -> str:
    """Load Inez's skill/system prompt from disk."""
    try:
        return SKILL_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Inez, Chief of Staff for the Smith Capital Portfolio."


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
        from core.database import _db_connection as _dbc
        _conn = _dbc()
        try:
            _rows = _conn.execute(
                "SELECT id,title,priority,status,project,due_date,assigned_agent FROM todos "
                "WHERE status IN ('pending','in_progress') ORDER BY priority ASC LIMIT 30"
            ).fetchall()
            todos = [dict(r) for r in _rows]
        finally:
            _conn.close()
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


# ── Email tools ───────────────────────────────────────────────────────────────

_EMAIL_READ_PATTERNS = [
    r"check(?:ing)?\s+(?:my\s+)?(?:email|inbox|mail|messages?)",
    r"(?:any\s+)?(?:new\s+)?emails?(?:\s+from)?",
    r"read\s+(?:my\s+)?(?:email|inbox|mail)",
    r"what'?s?\s+in\s+(?:my\s+)?(?:email|inbox|mail)",
    r"unread\s+(?:email|messages?|mail)",
    r"email\s+summary",
    r"inbox\s+summary",
    r"(?:search|find|look\s+for)\s+emails?",
    r"show\s+(?:me\s+)?(?:my\s+)?(?:email|inbox)",
]

_EMAIL_SEND_PATTERNS = [
    r"send\s+(?:an?\s+)?email",
    r"email\s+(?:to\s+)?[\w.+-]+@",
    r"write\s+(?:an?\s+)?email",
    r"draft\s+(?:an?\s+)?email",
    r"reply\s+to\s+(?:the\s+)?email",
    r"compose\s+(?:an?\s+)?email",
    r"forward\s+(?:the\s+)?email",
]


def _is_email_read_request(msg: str) -> bool:
    return any(re.search(p, msg, re.IGNORECASE) for p in _EMAIL_READ_PATTERNS)


def _is_email_send_request(msg: str) -> bool:
    return any(re.search(p, msg, re.IGNORECASE) for p in _EMAIL_SEND_PATTERNS)


def _load_email_awareness() -> str:
    """Return a formatted block of connected email accounts for Inez's system prompt."""
    if not DB_OK:
        return ""
    try:
        connectors = db.list_connectors()
        if not connectors:
            return "EMAIL ACCOUNTS: None connected. User can add them in Connector tab."
        lines = ["CONNECTED EMAIL ACCOUNTS (Inez has read + send access to these):"]
        for c in connectors:
            status = c.get("status", "unknown")
            email = c.get("email_address", "") or c.get("username", "")
            provider = c.get("provider", "")
            auth = c.get("auth_type", "")
            icon = "✅" if status == "active" else ("⚠️" if status == "error" else "🔄")
            lines.append(f"  {icon} {email} ({provider}, {auth}) — {status}  [id: {c.get('id','')}]")
        return "\n".join(lines)
    except Exception:
        return ""


def _pick_connector(user_message: str) -> "dict | None":
    """
    Pick the best matching active connector for a user message.
    Priority:
      1. Connector whose email_address or label matches keywords in the message
      2. Connector labelled 'personal', 'primary', 'main', or containing the user's name
      3. First active connector (fallback)
    """
    if not DB_OK:
        return None
    try:
        connectors = [c for c in db.list_connectors() if c.get("status") == "active"]
    except Exception:
        return None
    if not connectors:
        return None
    if len(connectors) == 1:
        return connectors[0]

    msg_lower = user_message.lower()

    # Step 1: direct mention of email address or label
    for c in connectors:
        addr = (c.get("email_address", "") or "").lower()
        label = (c.get("label", "") or "").lower()
        if addr and addr in msg_lower:
            return c
        if label and label in msg_lower:
            return c
    # Step 1b: partial label words (e.g. "sigma", "gulf", "personal")
    for c in connectors:
        label = (c.get("label", "") or "").lower()
        for word in label.split():
            if len(word) > 3 and word in msg_lower:
                return c

    # Step 2: prefer connectors labelled as primary/personal
    _primary_hints = ("personal", "primary", "main", "david", "smith")
    for hint in _primary_hints:
        for c in connectors:
            label = (c.get("label", "") or "").lower()
            addr = (c.get("email_address", "") or "").lower()
            if hint in label or hint in addr:
                return c

    # Step 3: fallback — first active
    return connectors[0]


# Keep old name as alias for callers that don't have a message
def _get_active_connector() -> "dict | None":
    """Return first active connector (use _pick_connector for context-aware selection)."""
    if not DB_OK:
        return None
    try:
        for c in db.list_connectors():
            if c.get("status") == "active":
                return c
    except Exception:
        pass
    return None


def _fetch_inbox_context(connector: dict, limit: int = 15) -> str:
    """Fetch recent emails via IMAP and return a formatted context block for Inez."""
    import imaplib
    import email as _email_lib
    from email.header import decode_header as _decode_header
    import base64 as _b64
    import json as _json

    email_addr = connector.get("email_address", "") or connector.get("username", "")
    label = connector.get("label", "") or email_addr
    auth_type = connector.get("auth_type", "password")
    imap_host = connector.get("imap_host", "")
    imap_port = int(connector.get("imap_port", 993) or 993)

    if not imap_host:
        return f"[EMAIL TOOL] No IMAP host configured for {email_addr}."

    try:
        def _decode_header_val(val: str) -> str:
            if not val:
                return ""
            parts = []
            for b, enc in _decode_header(val):
                if isinstance(b, bytes):
                    parts.append(b.decode(enc or "utf-8", errors="replace"))
                else:
                    parts.append(str(b))
            return " ".join(parts)

        imap = imaplib.IMAP4_SSL(imap_host, imap_port)

        if auth_type == "oauth2":
            try:
                from oauth_connector import get_valid_access_token  # type: ignore
                access_token = get_valid_access_token(connector["id"])
            except Exception as _tok_err:
                logger.warning("Token refresh failed: %s", _tok_err)
                return f"[EMAIL TOOL] Token error for {email_addr}: {_tok_err}. Re-authorize in Connector tab."
            # imaplib.authenticate() base64-encodes the callback return value itself —
            # return raw bytes, NOT pre-base64-encoded string
            raw_auth = f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01".encode()
            imap.authenticate("XOAUTH2", lambda _: raw_auth)
        else:
            creds_raw = connector.get("credentials", {})
            if isinstance(creds_raw, str):
                try:
                    creds_raw = _json.loads(creds_raw)
                except Exception:
                    creds_raw = {}
            password = creds_raw.get("password", "")
            imap.login(connector.get("username", email_addr), password)

        imap.select("INBOX")
        _, unseen_data = imap.search(None, "UNSEEN")
        unread_ids = set(unseen_data[0].split()) if unseen_data[0] else set()
        _, all_data = imap.search(None, "ALL")
        all_ids = all_data[0].split() if all_data[0] else []
        recent_ids = all_ids[-limit:] if len(all_ids) >= limit else all_ids

        lines = [
            f"[EMAIL INBOX — {label} <{email_addr}>]",
            f"Total messages: {len(all_ids)}  |  Unread: {len(unread_ids)}",
            "",
        ]
        for msg_id in reversed(recent_ids):
            try:
                _, msg_data = imap.fetch(
                    msg_id,
                    "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                )
                for part in msg_data:
                    if isinstance(part, tuple):
                        msg = _email_lib.message_from_bytes(part[1])
                        subject = _decode_header_val(msg.get("Subject", "(no subject)"))[:80]
                        sender = _decode_header_val(msg.get("From", ""))[:60]
                        date = (msg.get("Date", "") or "")[:30]
                        flag = "●" if msg_id in unread_ids else " "
                        lines.append(f"{flag} [{date}] {sender} — {subject}")
            except Exception:
                continue

        imap.logout()
        return "\n".join(lines)
    except Exception as e:
        return f"[EMAIL TOOL] IMAP error for {email_addr}: {e}"


def _extract_email_send_params(msg: str) -> dict:
    """Parse to/subject/body from a natural-language send-email request."""
    result = {"to": "", "subject": "", "body": ""}
    to_match = re.search(r"\bto\s+([\w.+-]+@[\w.+-]+\.\w+)", msg, re.IGNORECASE)
    if to_match:
        result["to"] = to_match.group(1)
    subj_match = re.search(
        r"(?:subject[:\s]+|with subject\s+)[\"']?(.+?)[\"']?(?=\n|body|message|$)",
        msg, re.IGNORECASE
    )
    if subj_match:
        result["subject"] = subj_match.group(1).strip()[:120]
    body_match = re.search(
        r"(?:body[:\s]+|message[:\s]+|saying[:\s]+|content[:\s]+)[\"']?(.+)",
        msg, re.IGNORECASE | re.DOTALL
    )
    if body_match:
        result["body"] = body_match.group(1).strip()
    return result


def _send_email_tool(connector: dict, to: str, subject: str, body: str) -> str:
    """Send an email via SMTP and return a status string."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import base64 as _b64
    import json as _json

    email_addr = connector.get("email_address", "") or connector.get("username", "")
    auth_type = connector.get("auth_type", "password")
    smtp_host = connector.get("smtp_host", "")
    smtp_port = int(connector.get("smtp_port", 587) or 587)

    if not smtp_host:
        return f"[EMAIL SEND FAILED] No SMTP host configured for {email_addr}."

    try:
        mime_msg = MIMEMultipart("alternative")
        mime_msg["From"] = email_addr
        mime_msg["To"] = to
        mime_msg["Subject"] = subject
        mime_msg.attach(MIMEText(body, "plain"))

        smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        if auth_type == "oauth2":
            try:
                from oauth_connector import get_valid_access_token  # type: ignore
                access_token = get_valid_access_token(connector["id"])
            except Exception as _tok_err:
                logger.warning("SMTP token refresh failed: %s", _tok_err)
                return f"[EMAIL SEND FAILED] Token error for {email_addr}: {_tok_err}. Re-authorize in Connector tab."
            # SMTP AUTH XOAUTH2 requires pre-base64-encoded auth string
            auth_str = _b64.b64encode(
                f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01".encode()
            ).decode()
            smtp.docmd("AUTH", f"XOAUTH2 {auth_str}")
        else:
            creds_raw = connector.get("credentials", {})
            if isinstance(creds_raw, str):
                try:
                    creds_raw = _json.loads(creds_raw)
                except Exception:
                    creds_raw = {}
            smtp.login(connector.get("username", email_addr), creds_raw.get("password", ""))

        smtp.sendmail(email_addr, [to], mime_msg.as_string())
        smtp.quit()
        return f"[EMAIL SENT] ✅ Sent to {to} | Subject: {subject}"
    except Exception as e:
        return f"[EMAIL SEND FAILED] {e}"


# ── Agent reports + run context ───────────────────────────────────────────────

def _load_active_reports_context() -> str:
    """Load running agent jobs and recent completed reports for Inez's awareness."""
    if not DB_OK:
        return ""
    lines = []
    try:
        recent_runs = db.list_runs(limit=20) if hasattr(db, "list_runs") else []
        running = [r for r in recent_runs if r.get("status") in ("running", "queued")]
        completed = [r for r in recent_runs if r.get("status") in ("completed", "complete")][:5]
        if running:
            lines.append(f"ACTIVE AGENT RUNS ({len(running)} running/queued):")
            for r in running[:5]:
                lines.append(f"  🟡 {r.get('agent_id','')} — {r.get('task','')[:80]} [{r.get('status','')}]")
        if completed:
            lines.append(f"\nRECENT COMPLETED RUNS ({len(completed)}):")
            for r in completed[:3]:
                score = f" | score: {r.get('reflexion_score','')}" if r.get("reflexion_score") else ""
                lines.append(f"  ✅ {r.get('agent_id','')} — {r.get('task','')[:60]}{score}")
    except Exception:
        pass
    try:
        reports = db.list_reports(limit=10)
        if reports:
            lines.append(f"\nRECENT REPORTS ({len(reports)}):")
            for rpt in reports[:5]:
                proj = f" ({rpt.get('project_slug','')})" if rpt.get("project_slug") else ""
                gen_by = f" by {rpt.get('generated_by','')}" if rpt.get("generated_by") else ""
                date = (rpt.get("generated_at", "") or "")[:10]
                summary_snip = (rpt.get("summary", "") or "")[:80]
                lines.append(f"  📄 [{date}] {rpt.get('title','')}{proj}{gen_by}")
                if summary_snip:
                    lines.append(f"       {summary_snip}")
    except Exception:
        pass
    return "\n".join(lines) if lines else ""


def _build_proactive_awareness() -> str:
    """
    Scan DB for items Inez should proactively surface:
    - Urgent/high todos
    - Todos with approaching due dates
    - Active agent runs + recent reports
    - Email account errors
    Returns a formatted awareness block injected into every prompt.
    """
    if not DB_OK:
        return ""
    lines = []
    _pending_todos = []
    try:
        from core.database import _db_connection as _dbc
        _conn = _dbc()
        try:
            _rows = _conn.execute(
                "SELECT id,title,priority,status,project,due_date FROM todos "
                "WHERE status='pending' ORDER BY priority ASC LIMIT 50"
            ).fetchall()
            _pending_todos = [dict(r) for r in _rows]
        finally:
            _conn.close()
    except Exception:
        pass

    try:
        urgent = [t for t in _pending_todos if t.get("priority") in ("urgent", "high")][:8]
        if urgent:
            lines.append("PRIORITY ITEMS NEEDING ATTENTION:")
            for t in urgent:
                due = f" [due {t.get('due_date')}]" if t.get("due_date") else ""
                proj = f" ({t.get('project','')})" if t.get("project") else ""
                lines.append(f"  [{t.get('priority','').upper()}] {t.get('title','')}{proj}{due}")
    except Exception:
        pass

    try:
        from datetime import timedelta
        week_out = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        due_soon = [t for t in _pending_todos
                    if t.get("due_date") and t["due_date"] <= week_out][:5]
        if due_soon:
            lines.append("\nDUE THIS WEEK:")
            for t in due_soon:
                lines.append(f"  • {t.get('title','')} — due {t.get('due_date','')} ({t.get('project','')})")
    except Exception:
        pass

    # Active runs + recent reports
    reports_block = _load_active_reports_context()
    if reports_block:
        lines.append("\n" + reports_block)

    # Email connector errors
    try:
        connectors = db.list_connectors()
        errored = [c for c in connectors if c.get("status") == "error"]
        if errored:
            lines.append("\nEMAIL CONNECTOR ALERTS:")
            for c in errored:
                lines.append(f"  ⚠️ {c.get('email_address','')} — authorization error. Re-authorize in Connector tab.")
    except Exception:
        pass

    return "\n".join(lines) if lines else ""


def _load_global_memory_block() -> str:
    """Load top-N facts from global_memory table for injection into system prompt."""
    try:
        import global_memory as gm
        block = gm.build_memory_block(n=20)
        # Track usage so important facts surface higher over time
        facts = gm.load_top_facts(n=20)
        gm.increment_usage([f["id"] for f in facts])
        return block
    except Exception:
        return ""


def _build_system_prompt(history: list[dict], cache_key: str = "default") -> str:
    """Build Inez's full system prompt with live context injected from DB."""
    _now = _time.monotonic()
    if cache_key in _PROMPT_CACHE:
        cached_prompt, cached_at = _PROMPT_CACHE[cache_key]
        if _now - cached_at < _PROMPT_CACHE_TTL:
            return cached_prompt

    skill = _load_skill()
    todos = _load_todos_context()
    memory = _load_memory_context()
    conv = _format_conversation_history(history)
    awareness = _build_proactive_awareness()

    # Pull full portfolio context from DB (replaces file-based client roster)
    portfolio = _load_portfolio_context()
    client_roster = _load_client_roster() if not portfolio else ""

    full_memory = "\n\n".join(filter(None, [portfolio, client_roster, memory])) or "No prior memory."

    # Global persistent memory — top 20 facts across all sessions
    global_mem_block = _load_global_memory_block()
    global_mem_section = f"\n\n{global_mem_block}" if global_mem_block else ""

    awareness_block = (
        f"\n\nPROACTIVE AWARENESS (items surfaced automatically — reference these when relevant):\n{awareness}"
        if awareness else ""
    )

    travel_tools_note = (
        "\n\nTRAVEL TOOLS: When the user asks to plan/create a trip or find hotels, "
        "a pre-execution tool has already geocoded the destination and searched for nearby hotels via OpenStreetMap. "
        "The results will appear in [TOOL RESULTS] in the user message. "
        "Present the hotel list clearly, note which ones have websites/phone numbers, "
        "and confirm the trip has been saved to the Travel tab."
    )

    # Email accounts awareness (always injected so Inez knows what's available)
    email_awareness = _load_email_awareness()
    email_section = f"\n\n{email_awareness}" if email_awareness else ""

    email_tools_note = (
        "\n\nEMAIL TOOLS: You have direct read and send access to the connected email accounts listed above.\n"
        "• When the user asks to check, summarize, or search email — a pre-execution IMAP tool fetches the inbox.\n"
        "  Results appear in [EMAIL INBOX TOOL DATA] in the user message. Present them as a clean summary.\n"
        "• When the user asks you to send/compose/reply to an email — a pre-execution SMTP tool attempts the send.\n"
        "  Results appear in [EMAIL SEND TOOL DATA]. Confirm success or report the error.\n"
        "• You can reference which account was used and offer to use a specific account if multiple are connected.\n"
        "• For reports: agent run results and report summaries appear in PROACTIVE AWARENESS above — "
        "  reference them when summarizing what agents have completed or what reports are ready."
    ) if email_awareness else ""

    base = (
        skill
        .replace("{todos_context}", todos)
        .replace("{memory_context}", full_memory)
        .replace("{conversation_history}", conv)
    )
    result = (
        DAVID_PROFILE + "\n\n" + base
        + global_mem_section
        + email_section
        + awareness_block
        + travel_tools_note
        + email_tools_note
    )
    _PROMPT_CACHE[cache_key] = (result, _time.monotonic())
    return result


def _normalize_agent_id(agent_id: str) -> str:
    """
    Map a potentially hallucinated agent_id to the closest registered agent.
    Strategy (in order):
      1. Exact match
      2. Normalised match (strip hyphens/underscores/spaces, lowercase)
      3. Substring match on normalised form
      4. Word-in-ID match: split hallucinated ID on word boundaries, check each
         word appears as substring in a registered ID. Highest hit count wins.
    """
    try:
        agents = db.list_agents()
        registered = {a["agent_id"]: a for a in agents if a.get("agent_id")}
    except Exception:
        return agent_id

    if agent_id in registered:
        return agent_id

    def _norm(s: str) -> str:
        return re.sub(r"[-_\s]", "", s.lower())

    norm_id = _norm(agent_id)

    # Exact normalised match (e.g. "wordpress-agent" == "wordpressagent")
    for rid in registered:
        if _norm(rid) == norm_id:
            return rid

    # Substring on normalised form
    for rid in registered:
        norm_rid = _norm(rid)
        if norm_id in norm_rid or norm_rid in norm_id:
            return rid

    # Word-in-ID: split hallucinated id into words, score by how many words
    # appear as substrings inside each registered id (handles "wordpress-expert" → "wordpressagent")
    words = [w.lower() for w in re.split(r"[-_\s]", agent_id) if len(w) > 2]
    if words:
        best, best_score = None, 0
        for rid in registered:
            rid_lower = rid.lower()
            score = sum(1 for w in words if w in rid_lower)
            if score > best_score:
                best_score, best = score, rid
        if best and best_score > 0:
            return best

    return agent_id  # keep original if nothing matches


def _parse_inez_response(raw: str) -> dict:
    """
    Extract structured response from Inez.
    Handles: JSON code block, markdown bold-section format, [TASK:]/[TODO:] markers.
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

    def _apply_dispatch_data(data: dict) -> bool:
        """Populate result from a parsed dispatch dict. Returns True on success."""
        if "inez_message" not in data and "dispatches" not in data:
            return False
        msg = data.get("inez_message", "")
        # Strip **inez_message**: prefix if LLM echoed it inside the value
        msg = re.sub(r"^\*\*inez_message\*\*:\s*", "", msg).strip().strip('"')
        result["inez_message"] = msg
        dispatches = data.get("dispatches", [])
        # Normalise agent_ids so hallucinated names map to real ones
        for d in dispatches:
            if isinstance(d, dict) and d.get("agent_id"):
                d["agent_id"] = _normalize_agent_id(d["agent_id"])
        result["dispatches"] = dispatches
        result["needs_agents"] = bool(dispatches)
        return True

    # ── Strategy 1: JSON inside a code fence ──────────────────────────────
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean, re.DOTALL)
    if json_match:
        try:
            if _apply_dispatch_data(json.loads(json_match.group(1))):
                return result
        except json.JSONDecodeError:
            pass

    # ── Strategy 2: bare top-level JSON object containing "inez_message" ──
    bare_match = re.search(r"(\{[\s\S]*\"inez_message\"[\s\S]*\})", clean, re.DOTALL)
    if bare_match:
        try:
            if _apply_dispatch_data(json.loads(bare_match.group(1))):
                return result
        except json.JSONDecodeError:
            pass

    # ── Strategy 3: markdown bold-section format ───────────────────────────
    # e.g. **inez_message**: "..." \n **dispatches**: [...] \n **needs_agents**: true
    msg_match = re.search(
        r"\*\*inez_message\*\*\s*:\s*[\"']?(.*?)[\"']?\s*(?=\n\*\*|\Z)", clean, re.DOTALL | re.IGNORECASE
    )
    disp_match = re.search(r"\*\*dispatches\*\*\s*:\s*(\[[\s\S]*?\])\s*(?=\n\*\*|\Z)", clean, re.DOTALL | re.IGNORECASE)

    if msg_match or disp_match:
        if msg_match:
            result["inez_message"] = msg_match.group(1).strip().strip('"').strip("'")
        if disp_match:
            try:
                dispatches = json.loads(disp_match.group(1))
                for d in dispatches:
                    if isinstance(d, dict) and d.get("agent_id"):
                        d["agent_id"] = _normalize_agent_id(d["agent_id"])
                result["dispatches"] = dispatches
                result["needs_agents"] = bool(dispatches)
            except json.JSONDecodeError:
                pass
        if result["inez_message"] or result["dispatches"]:
            return result

    # ── Fallback: treat entire clean response as inez_message ─────────────
    result["inez_message"] = clean
    return result


def _generate_followups(user_question: str, inez_response: str) -> list[str]:
    """
    Generate 3-5 follow-up question suggestions based on the conversation.
    
    These suggestions help the user explore the topic deeper without having to
    think of the next question themselves.
    
    Args:
        user_question: The original question the user asked
        inez_response: Inez's answer to that question
        
    Returns:
        List of 3-5 follow-up questions as strings, or empty list on error
    """
    if not LLM_OK:
        return []
    
    try:
        # Only reached when a fast backend is active (see _is_slow_local_provider
        # gate in think). weight="heavy" routes it to the same fast free key.
        model = _llm(temperature=0.7, weight="heavy")  # Higher temp for creativity
        
        prompt = f"""You are Inez, Chief of Staff for David Smith's portfolio of ventures.

The user just asked: "{user_question}"

You responded: "{inez_response[:500]}..."

Generate 3-5 specific, actionable follow-up questions the user might want to ask next.

RULES:
- Make questions concrete and specific (not generic like "Tell me more")
- Anticipate natural next steps in the conversation
- Consider David's roles: HP Engineering, XFTC, S2T Designs, PBS Foundation, Markets, Ministry
- Mix depth (go deeper on same topic) and breadth (explore related topics)
- Keep questions under 100 characters each
- Don't repeat information already covered

Format as a JSON array of strings:
["First follow-up question?", "Second question?", "Third question?"]

ONLY return the JSON array, nothing else."""

        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)
        
        # Extract JSON array
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        followups = json.loads(raw)
        
        # Validate
        if isinstance(followups, list) and all(isinstance(q, str) for q in followups):
            # Limit to 5 questions
            return followups[:5]
        else:
            logger.warning("Follow-up suggestions not in expected format")
            return []
            
    except Exception as e:
        logger.error("Error generating follow-ups: %s", e)
        return []


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

    # ── Step 1a: Travel pre-fetch ─────────────────────────────────────────────
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

    # ── Step 1b: Email read pre-fetch ─────────────────────────────────────────
    email_read_data = ""
    if _is_email_read_request(user_message):
        try:
            connector = _pick_connector(user_message)
            if connector:
                label = connector.get("label", "") or connector.get("email_address", "")
                if emit:
                    emit("inez_thinking", message=f"Fetching inbox for {label}...")
                email_read_data = _fetch_inbox_context(connector, limit=20)
            else:
                email_read_data = "[EMAIL TOOL] No active email accounts connected. Go to Connector tab to add one."
        except Exception as _ee:
            logger.warning("Email read pre-fetch error: %s", _ee)

    # ── Step 1c: Email send tool ──────────────────────────────────────────────
    email_send_data = ""
    if _is_email_send_request(user_message):
        try:
            connector = _pick_connector(user_message)
            if connector:
                params = _extract_email_send_params(user_message)
                if params.get("to") and params.get("subject") and params.get("body"):
                    if emit:
                        emit("inez_thinking", message=f"Sending email to {params['to']}...")
                    email_send_data = _send_email_tool(
                        connector,
                        to=params["to"],
                        subject=params["subject"],
                        body=params["body"],
                    )
                else:
                    # Not enough params extracted — let Inez ask for them
                    email_send_data = (
                        "[EMAIL SEND TOOL] Couldn't extract full send parameters from request. "
                        "Need: recipient email address, subject, and body to send."
                    )
            else:
                email_send_data = "[EMAIL SEND TOOL] No active email account connected."
        except Exception as _se:
            logger.warning("Email send tool error: %s", _se)

    # ── Step 1d: Web search tool ──────────────────────────────────────────────
    web_search_data = ""
    web_search_sources = []
    web_search_query = None
    if WEB_SEARCH_OK and SearchAnalyzer.should_search(user_message):
        try:
            # Try environment variable first, then database config
            api_key = os.environ.get("SERPAPI_API_KEY")
            if not api_key and DB_OK:
                api_key = db.get_config("serpapi_api_key")
            
            if api_key:
                if emit:
                    emit("inez_thinking", message="🌐 Searching the web...")
                client = SerpAPIClient(api_key)
                search_result = client.search(user_message, num_results=5)
                if search_result.sources:
                    web_search_sources = search_result.sources
                    web_search_query = user_message
                    lines = [f"[WEB SEARCH RESULTS for: '{user_message}']"]
                    for source in search_result.sources:
                        lines.append(f"\n[{source.id}] {source.title}")
                        lines.append(f"    {source.snippet}")
                        lines.append(f"    Source: {source.url}")
                    web_search_data = "\n".join(lines)
                    web_search_data += (
                        "\n\nINSTRUCTIONS: Use these web sources to provide accurate, up-to-date information. "
                        "Cite sources inline using [cite:N] where N is the source number. "
                        "Example: 'Tesla is trading at $242 [cite:1]'"
                    )
                    if emit:
                        emit("inez_thinking", message=f"✅ Found {len(search_result.sources)} sources")
            else:
                logger.info("SERPAPI_API_KEY not configured — web search skipped")
        except Exception as _ws:
            logger.warning("Web search error: %s", _ws)

    conv_id = history[0].get("conversation_id", "default") if history else "default"
    system_prompt = _build_system_prompt(history, cache_key=conv_id[:16])

    # ── Step 2: Inez analysis — determines what to say and who to dispatch ────
    # Build a concise agent roster for dispatch guidance
    _agent_roster_lines = []
    try:
        _all_agents = db.list_agents()
        for _a in _all_agents:
            _aid = _a.get("agent_id", "")
            _name = _a.get("name", "")
            _desc = str(_a.get("description", ""))[:80]
            if _aid and _aid not in ("inez-chief-of-staff",):
                _agent_roster_lines.append(f"  - {_aid}: {_name}" + (f" — {_desc}" if _desc else ""))
    except Exception:
        pass
    _roster_block = (
        "\n\nAVAILABLE AGENTS (use exact agent_id values when dispatching):\n"
        + ("\n".join(_agent_roster_lines) if _agent_roster_lines else "  (none registered)")
    )

    dispatch_instructions = (
        "\n\nDISPATCH INSTRUCTIONS: When you need agents to do work, respond ONLY with this exact JSON format"
        " (no markdown, no bold headers, just the JSON code block):\n"
        "```json\n"
        '{"inez_message": "Brief summary of what you are doing and why.", '
        '"dispatches": [{"agent_id": "exact-agent-id-from-list", "task": "specific task description", '
        '"project": "project-slug", "context": "any extra context the agent needs"}]}\n'
        "```\n"
        "EXAMPLE — user asks 'have the wordpress expert audit our site':\n"
        "```json\n"
        '{"inez_message": "Dispatching the WordPress agent to audit your site.", '
        '"dispatches": [{"agent_id": "wordpressagent", "task": "Audit site for performance and SEO issues", '
        '"project": "web", "context": ""}]}\n'
        "```\n"
        "RULES:\n"
        "- Use ONLY agent_id values from the AVAILABLE AGENTS list below — never invent or paraphrase them.\n"
        "- If no agent dispatch is needed, respond in plain text (no JSON block).\n"
        "- For travel: travel-project-lead (orchestrator), travel-hotel-agent (lodging), "
        "travel-flights-agent (flights), travel-budget-helper (budget).\n"
        + _roster_block
    )

    augmented_message = user_message
    extra_blocks = []
    if travel_tool_data:
        extra_blocks.append(f"[PRE-FETCHED TRAVEL DATA — pass this to the travel agent as context]:\n{travel_tool_data}")
    if email_read_data:
        extra_blocks.append(f"[EMAIL INBOX TOOL DATA]:\n{email_read_data}")
    if email_send_data:
        extra_blocks.append(f"[EMAIL SEND TOOL DATA]:\n{email_send_data}")
    if web_search_data:
        extra_blocks.append(web_search_data)
    if extra_blocks:
        augmented_message = user_message + "\n\n" + "\n\n".join(extra_blocks)

    try:
        model = _llm(temperature=0.3, weight="heavy")  # main reasoning → fast free key if available
        messages = [
            SystemMessage(content=system_prompt + dispatch_instructions),
            HumanMessage(content=augmented_message),
        ]
        # The reasoning call can take tens of seconds on a local CPU model; surface
        # a status step so the UI shows progress instead of a silent wait.
        if emit:
            emit("inez_thinking", message="Consulting the AI engine…")
        response = model.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        result = _parse_inez_response(raw)
        result["error"] = None
        result.setdefault("agent_results", [])
        
        # ── Format citations if web search was used ───────────────────────────
        if WEB_SEARCH_OK and web_search_sources:
            try:
                inez_msg = result.get("inez_message", "")
                formatted = CitationFormatter.format_with_citations(inez_msg, web_search_sources)
                result["inez_message"] = formatted
                result["has_citations"] = True
                result["citations"] = [
                    {
                        "id": s.id,
                        "title": s.title,
                        "url": s.url,
                        "snippet": s.snippet,
                    }
                    for s in web_search_sources
                ]
                result["search_query"] = web_search_query
            except Exception as _cf:
                logger.warning("Citation formatting error: %s", _cf)
                # Keep unformatted message if citation formatting fails
                result["has_citations"] = False

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
                # Pass Inez's fast model down so dispatched agents don't grind on
                # the dead-free-key → slow-Ollama path (keeps dispatch scoped to
                # Inez's interactive model without changing background routing).
                agent_results = run_dispatches(dispatches, emit=emit, llm=model)
                result["agent_results"] = agent_results

                # ── Step 4: Synthesis — Inez reads all agent outputs ──────────
                synthesis_context = build_synthesis_context(agent_results)
                if synthesis_context:
                    if emit:
                        emit("inez_thinking", message="Synthesizing results...")
                    synth_messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=(
                            f"Original request: {user_message}\n\n"
                            f"{synthesis_context}\n\n"
                            "Provide your final synthesized response as Inez, Chief of Staff:\n"
                            "1. One sentence of situational awareness (what happened, what it means)\n"
                            "2. Key findings or outputs — be specific, name the things\n"
                            "3. Your recommendation for next action\n"
                            "Be concise. Lead with the most important thing. "
                            "Reference what was saved to the database where relevant."
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
            # Trim exchange history to 50 most recent entries to prevent unbounded growth
            try:
                if hasattr(db, "get_conn"):
                    with db.get_conn() as _mc:
                        _mc.execute(
                            """DELETE FROM agent_memory
                               WHERE agent_id = ? AND key LIKE 'exchange_%'
                               AND key NOT IN (
                                   SELECT key FROM agent_memory
                                   WHERE agent_id = ? AND key LIKE 'exchange_%'
                                   ORDER BY updated_at DESC LIMIT 50
                               )""",
                            (INEZ_AGENT_ID, INEZ_AGENT_ID),
                        )
            except Exception:
                pass

        # ── Generate follow-up question suggestions ──────────────────────────
        # Skipped on slow local providers (Ollama on CPU): this is a second LLM
        # call, and stacking it after the main analysis call can push the request
        # past the reverse-proxy limit (~100s) and surface as a 524.
        if LLM_OK and result.get("inez_message") and not _is_slow_local_provider():
            try:
                if emit:
                    emit("inez_thinking", message="Generating follow-up suggestions...")
                followups = _generate_followups(user_message, result["inez_message"])
                if followups:
                    result["followup_suggestions"] = followups
            except Exception as _fs:
                logger.warning("Follow-up generation error: %s", _fs)
                # Non-critical — continue without suggestions

        # ── Progressive Intelligence: auto-extract memory + record patterns ──
        try:
            import progressive_intelligence as pi
            new_facts = pi.auto_extract_memory(user_message, result.get("inez_message", ""))
            if new_facts:
                logger.info("PI auto-extracted %d new memory facts from conversation", len(new_facts))
            # Record topic patterns from the conversation
            pi._record_topics_from_text(
                user_message + " " + result.get("inez_message", "")[:200],
                agent_id="inez",
                user_id="default",
            )
        except Exception:
            pass

        if emit:
            emit("inez_response",
                 message=result["inez_message"],
                 dispatches=result.get("dispatches", []),
                 followup_suggestions=result.get("followup_suggestions", []))

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
    Generate an Inez Chief of Staff morning briefing for David.
    Returns {"content": str, "error": str|None}
    """
    if not LLM_OK:
        return {"content": INEZ_FALLBACK, "error": "LLM not available"}

    system_prompt = _build_system_prompt(history or [])
    now = datetime.now()
    brief_request = (
        f"Generate David's morning briefing for {now.strftime('%A, %B %d')}.\n\n"
        "Respond as Inez, Chief of Staff — not a chatbot, not a list generator. "
        "You already reviewed everything. Lead with awareness.\n\n"
        "Format:\n"
        "**Good morning, David.** [One sentence — what the operational picture looks like right now.]\n\n"
        "**Priority Attention:**\n"
        "1. [Specific item] — [your recommendation]\n"
        "2. [Specific item] — [your recommendation]\n"
        "3. [Specific item] — [your recommendation]\n\n"
        "**Team Status:** [One sentence on what agents are executing or what's queued.]\n\n"
        "**My Recommendation:** [Single clearest next action for David today.]\n\n"
        "Pull from: urgent/high todos, approaching deadlines, active runs, client blockers. "
        "Name specific things — project names, client names, due dates. No vague categories."
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


def generate_status_report() -> dict:
    """
    Generate Inez's current awareness state — used by the /api/inez/status endpoint.
    Returns structured data for dashboard HUDs (iOS, Watch, Desktop).
    """
    awareness = _build_proactive_awareness()
    todos_context = _load_todos_context()

    urgent_count = 0
    try:
        urgent_count = len([t for t in db.list_todos(status="pending")
                            if t.get("priority") in ("urgent", "high")])
    except Exception:
        pass

    missions = []
    try:
        projects = db.list_projects()
        mission_order = [
            "archonhub", "xftc", "s2tdesigns", "pbs-foundation",
            "ministry", "smithcap-finance", "markets", "nutrue", "sigma-signal",
        ]
        proj_map = {p.get("slug", ""): p for p in projects}
        for slug in mission_order:
            p = proj_map.get(slug)
            if p:
                missions.append({
                    "name": p.get("name", slug),
                    "slug": slug,
                    "status": p.get("status", "active"),
                })
    except Exception:
        pass

    return {
        "awareness": awareness or "All systems nominal.",
        "urgent_count": urgent_count,
        "missions": missions[:6],
        "generated_at": datetime.now().isoformat(),
    }


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
