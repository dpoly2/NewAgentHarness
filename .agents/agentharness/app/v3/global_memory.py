"""
global_memory.py — Persistent cross-session memory engine for ArchonHub
========================================================================
Provides:
  • load_top_facts(n)     — top-N facts by importance+usage for prompt injection
  • build_memory_block()  — formatted string ready for system prompt injection
  • extract_and_store()   — auto-extract new facts from a conversation turn
  • upsert_fact()         — create or update a single fact
  • delete_fact()         — remove a fact by ID
  • list_facts()          — paginated list for UI / API
  • search_facts()        — keyword search across all facts
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).parent
DB_PATH = HERE.parent.parent / "memory" / "runs_v3.db"

# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = {
    "preferences": "Communication style, working preferences, likes/dislikes",
    "projects":    "Active projects, deadlines, launch dates, priorities",
    "people":      "Roles, relationships, team members, contacts",
    "deadlines":   "Hard dates, milestones, commitments",
    "ministry":    "Sermon topics, scripture focus, worship themes",
    "technical":   "Tech stack decisions, architecture choices, credentials context",
    "rules":       "Standing instructions, things to always or never do",
    "finance":     "Portfolio preferences, risk tolerance, financial goals",
}

# ── DB helper ─────────────────────────────────────────────────────────────────

def _get_conn():
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ── Core read functions ───────────────────────────────────────────────────────

def load_top_facts(n: int = 20, category: Optional[str] = None) -> list[dict]:
    """
    Return top-N facts ordered by importance DESC, usage_count DESC.
    Optionally filter to a single category.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if category:
            cur.execute(
                """
                SELECT id, category, key, value, importance, confidence, usage_count, source
                FROM global_memory
                WHERE category = ?
                ORDER BY importance DESC, usage_count DESC
                LIMIT ?
                """,
                (category, n),
            )
        else:
            cur.execute(
                """
                SELECT id, category, key, value, importance, confidence, usage_count, source
                FROM global_memory
                ORDER BY importance DESC, usage_count DESC
                LIMIT ?
                """,
                (n,),
            )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def build_memory_block(n: int = 20) -> str:
    """
    Build a formatted memory block for injection into any agent system prompt.
    Groups facts by category for readability.
    """
    facts = load_top_facts(n)
    if not facts:
        return ""

    by_category: dict[str, list[dict]] = {}
    for f in facts:
        by_category.setdefault(f["category"], []).append(f)

    # Category display order
    order = ["people", "projects", "deadlines", "preferences", "rules",
             "ministry", "finance", "technical"]
    sorted_cats = sorted(by_category.keys(), key=lambda c: order.index(c) if c in order else 99)

    lines = ["GLOBAL MEMORY (persistent facts — always consider these):"]
    for cat in sorted_cats:
        cat_facts = by_category[cat]
        lines.append(f"\n[{cat.upper()}]")
        for f in cat_facts:
            conf_marker = "" if f["confidence"] >= 0.9 else f" (confidence: {f['confidence']:.0%})"
            lines.append(f"  • {f['key']}: {f['value']}{conf_marker}")

    return "\n".join(lines)


def build_agent_memory_block(agent_type: str, n: int = 15) -> str:
    """
    Build a focused memory block for a specific agent type.
    Each agent gets relevant categories + global rules.
    """
    agent_category_map = {
        "markets":   ["finance", "projects", "people", "rules"],
        "finance":   ["finance", "people", "projects", "rules"],
        "legal":     ["people", "projects", "rules", "technical"],
        "research":  ["projects", "people", "technical", "rules"],
        "grants":    ["projects", "people", "rules"],
        "ministry":  ["ministry", "people", "preferences", "rules"],
        "inez":      None,  # gets all categories
    }
    categories = agent_category_map.get(agent_type)
    if categories is None:
        return build_memory_block(n)

    facts: list[dict] = []
    seen_ids: set[str] = set()
    per_cat = max(3, n // len(categories))
    for cat in categories:
        for f in load_top_facts(per_cat, category=cat):
            if f["id"] not in seen_ids:
                facts.append(f)
                seen_ids.add(f["id"])

    if not facts:
        return ""

    lines = [f"GLOBAL MEMORY — {agent_type.upper()} CONTEXT:"]
    by_category: dict[str, list[dict]] = {}
    for f in facts:
        by_category.setdefault(f["category"], []).append(f)
    for cat, cat_facts in by_category.items():
        lines.append(f"\n[{cat.upper()}]")
        for f in cat_facts:
            lines.append(f"  • {f['key']}: {f['value']}")
    return "\n".join(lines)


# ── Write functions ───────────────────────────────────────────────────────────

def upsert_fact(
    category: str,
    key: str,
    value: str,
    source: str = "user",
    confidence: float = 1.0,
    importance: int = 5,
    fact_id: Optional[str] = None,
) -> dict:
    """
    Insert or update a fact. Returns the saved fact dict.
    If (category, key) already exists, updates value + metadata.
    """
    now = _now()
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM global_memory WHERE category = ? AND key = ?",
            (category, key),
        )
        existing = cur.fetchone()

        if existing:
            fid = existing["id"]
            cur.execute(
                """
                UPDATE global_memory
                SET value=?, source=?, confidence=?, importance=?, updated_at=?
                WHERE id=?
                """,
                (value, source, confidence, importance, now, fid),
            )
        else:
            fid = fact_id or str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO global_memory
                  (id, category, key, value, source, confidence, importance,
                   last_verified, usage_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (fid, category, key, value, source, confidence, importance, now, now, now),
            )
        conn.commit()
        conn.close()
        return {"id": fid, "category": category, "key": key, "value": value,
                "source": source, "confidence": confidence, "importance": importance}
    except Exception as e:
        return {"error": str(e)}


def delete_fact(fact_id: str) -> bool:
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM global_memory WHERE id = ?", (fact_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def increment_usage(fact_ids: list[str]) -> None:
    """Increment usage_count for a list of facts (called after each injection)."""
    if not fact_ids:
        return
    try:
        conn = _get_conn()
        placeholders = ",".join("?" * len(fact_ids))
        conn.execute(
            f"UPDATE global_memory SET usage_count = usage_count + 1 WHERE id IN ({placeholders})",
            fact_ids,
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def list_facts(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        if category:
            cur.execute(
                """
                SELECT * FROM global_memory WHERE category = ?
                ORDER BY importance DESC, usage_count DESC
                LIMIT ? OFFSET ?
                """,
                (category, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT * FROM global_memory
                ORDER BY importance DESC, usage_count DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def search_facts(query: str, limit: int = 20) -> list[dict]:
    """Keyword search across key + value fields."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        q = f"%{query}%"
        cur.execute(
            """
            SELECT * FROM global_memory
            WHERE key LIKE ? OR value LIKE ?
            ORDER BY importance DESC
            LIMIT ?
            """,
            (q, q, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def get_fact(fact_id: str) -> Optional[dict]:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM global_memory WHERE id = ?", (fact_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def count_facts() -> dict[str, int]:
    """Return fact counts per category."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT category, COUNT(*) as cnt FROM global_memory GROUP BY category"
        )
        result = {row["category"]: row["cnt"] for row in cur.fetchall()}
        conn.close()
        return result
    except Exception:
        return {}


# ── Auto-extraction ───────────────────────────────────────────────────────────

# Patterns for extracting facts from conversation text
_EXTRACTION_PATTERNS = [
    # Deadlines / dates
    (r"(?:launch|release|deploy|ship|due|deadline)[:\s]+(.{5,80})\s+(?:on|by)\s+([\w\s,]+\d{4})",
     "deadlines", "deadline"),
    # Preferences stated explicitly
    (r"(?:i prefer|i want|i like|i always|i never|i need|i don't want)\s+(.{5,120})",
     "preferences", "stated_preference"),
    # Project mentions
    (r"(?:working on|building|launching|developing)\s+(.{5,80})",
     "projects", "active_work"),
]


def extract_and_store(user_message: str, agent_response: str, source: str = "agent_learned") -> list[dict]:
    """
    Attempt to extract learnable facts from a conversation turn.
    Uses the LLM if available; falls back to regex patterns.
    Returns list of newly stored/updated facts.
    """
    stored: list[dict] = []

    # Try LLM extraction first
    try:
        stored = _llm_extract(user_message, agent_response, source)
        if stored:
            return stored
    except Exception:
        pass

    # Fallback: regex extraction
    for pattern, category, key_prefix in _EXTRACTION_PATTERNS:
        for match in re.finditer(pattern, user_message, re.IGNORECASE):
            value = match.group(1).strip().rstrip(".,;")
            if len(value) < 5 or len(value) > 200:
                continue
            key = f"{key_prefix}_{_slug(value[:30])}"
            result = upsert_fact(
                category=category,
                key=key,
                value=value,
                source=source,
                confidence=0.7,
                importance=5,
            )
            if "error" not in result:
                stored.append(result)

    return stored


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _llm_extract(user_message: str, agent_response: str, source: str) -> list[dict]:
    """Use OpenAI to extract structured facts from a conversation turn."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return []

    import openai
    client = openai.OpenAI(api_key=api_key)

    categories_str = "\n".join(f"  - {k}: {v}" for k, v in CATEGORIES.items())
    prompt = f"""You are a memory extraction system. Extract ONLY clear, durable, factual statements that would help an AI assistant serve this user better in future conversations.

Categories:
{categories_str}

Conversation:
USER: {user_message[:500]}
ASSISTANT: {agent_response[:500]}

Extract facts as JSON array. Each fact: {{"category": "...", "key": "...", "value": "...", "importance": 1-10}}
- key: snake_case label (e.g., "sermon_prep_day", "preferred_llm_model")
- value: clear statement (e.g., "David preps sermons on Saturday mornings")
- importance: 1-10 (10 = critical to all interactions)
- Only extract facts explicitly stated or strongly implied
- Skip trivial, session-specific, or already-obvious facts
- Return [] if nothing worth extracting

Return ONLY valid JSON array, no explanation."""

    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()

    extracted = json.loads(raw)
    if not isinstance(extracted, list):
        return []

    stored = []
    for item in extracted:
        if not all(k in item for k in ("category", "key", "value")):
            continue
        if item["category"] not in CATEGORIES:
            continue
        result = upsert_fact(
            category=item["category"],
            key=item["key"],
            value=item["value"],
            source=source,
            confidence=0.85,
            importance=int(item.get("importance", 5)),
        )
        if "error" not in result:
            stored.append(result)

    return stored
