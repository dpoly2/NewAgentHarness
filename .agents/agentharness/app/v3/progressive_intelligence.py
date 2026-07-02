"""
progressive_intelligence.py — ArchonHub Progressive Intelligence Engine
=========================================================================
ArchonHub gets smarter with every interaction through four compounding layers:

  Layer 1 · Reflexion Scoring   — agent scores its own output after every run;
                                   if quality < 0.75, rewrites its skill file
  Layer 2 · Conversation Memory — every Inez reply auto-extracts new facts into
                                   Global Memory (deepening over time)
  Layer 3 · Skill Progression   — per-agent success rate drives prompt escalation
                                   novice → intermediate → expert → master
  Layer 4 · Pattern Detection   — recurring topics/timing → proactive briefings
                                   before the user even asks

Public API
----------
  reflexion_score_run(agent_id, task, output)  → dict
  auto_extract_memory(user_msg, agent_reply)   → list[dict]
  get_skill_level(agent_id)                    → str
  inject_skill_context(agent_id, prompt)       → str
  detect_patterns(user_id)                     → list[dict]
  record_interaction(agent_id, task, output, success, quality_score)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

HERE    = Path(__file__).parent
HARNESS = HERE.parent.parent
SKILLS  = HARNESS / "memory"

import sys
for _p in (HERE, HARNESS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import hub_db as db
    DB_PATH = db.DB_PATH
    DB_OK = True
except Exception:
    DB_PATH = HARNESS / "memory" / "runs_v3.db"
    DB_OK = False

# ── Constants ─────────────────────────────────────────────────────────────────

SKILL_THRESHOLDS = {
    "novice":       (0,   10,   0.0,  0.60),   # (min_runs, max_runs, min_rate, max_rate)
    "intermediate": (10,  50,   0.60, 0.80),
    "expert":       (50,  200,  0.80, 0.90),
    "master":       (200, 9999, 0.90, 1.01),
}

REFLEXION_THRESHOLD = 0.75   # score below this triggers skill file rewrite
PATTERN_MIN_OCCURRENCES = 3  # topic must appear ≥ N times to count as a pattern
PATTERN_WINDOW_DAYS = 30

# ── DB Helpers ────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    """Create progressive intelligence tables if they don't exist."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS agent_skill_levels (
            agent_id        TEXT PRIMARY KEY,
            total_runs      INTEGER DEFAULT 0,
            successful_runs INTEGER DEFAULT 0,
            avg_quality     REAL    DEFAULT 0.0,
            skill_level     TEXT    DEFAULT 'novice',
            last_reflexion  TEXT,
            updated_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS reflexion_log (
            id          TEXT PRIMARY KEY,
            agent_id    TEXT NOT NULL,
            run_id      TEXT,
            task        TEXT,
            output      TEXT,
            score       REAL,
            critique    TEXT,
            skill_rewritten INTEGER DEFAULT 0,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS interaction_patterns (
            id              TEXT PRIMARY KEY,
            user_id         TEXT DEFAULT 'default',
            topic           TEXT,
            agent_id        TEXT,
            occurrence_count INTEGER DEFAULT 1,
            last_seen       TEXT,
            first_seen      TEXT,
            typical_time    TEXT,
            proactive_sent  INTEGER DEFAULT 0
        );
        """)


_ensure_tables()

# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 · Reflexion Scoring
# ─────────────────────────────────────────────────────────────────────────────

_REFLEXION_PROMPT = """You are a quality evaluator for AI agent outputs.

Agent: {agent_id}
Task: {task}
Output: {output}

Score this output from 0.0 to 1.0 on:
- Completion (50%): Did the agent fully address the task?
- Quality (35%): Is the output accurate, well-structured, and useful?
- Efficiency (15%): Was the response concise and relevant?

Also write a 1-2 sentence critique identifying the main weakness (or "No significant weakness" if score >= 0.9).

Respond ONLY with valid JSON:
{{"score": 0.82, "completion": 0.85, "quality": 0.80, "efficiency": 0.75, "critique": "..."}}"""

_REWRITE_PROMPT = """You are improving an AI agent's skill file based on performance feedback.

Agent: {agent_id}
Current skill file:
{current_skill}

Recent critique:
{critique}

Recent task that scored {score:.2f}/1.0:
Task: {task}
Output: {output}

Rewrite the skill file to address the critique while keeping all valuable existing content.
Improve the agent's approach, add relevant examples or strategies, and remove any patterns that led to the low score.
Keep the same format and length (roughly). Return ONLY the updated skill file text."""


def reflexion_score_run(
    agent_id: str,
    task: str,
    output: str,
    run_id: str = "",
) -> dict:
    """
    Score an agent run using LLM-as-judge.
    If score < REFLEXION_THRESHOLD, rewrite the agent's skill file.
    Returns: {"score": float, "critique": str, "skill_rewritten": bool}
    """
    try:
        from hub_nodes import _llm
        from langchain_core.messages import SystemMessage, HumanMessage
    except Exception:
        return {"score": 1.0, "critique": "", "skill_rewritten": False}

    import uuid
    log_id = str(uuid.uuid4())

    # Score the output
    score = 1.0
    critique = ""
    try:
        model = _llm(temperature=0.1)
        prompt = _REFLEXION_PROMPT.format(
            agent_id=agent_id,
            task=task[:600],
            output=output[:1500],
        )
        resp = model.invoke([HumanMessage(content=prompt)])
        raw = resp.content if hasattr(resp, "content") else str(resp)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group())
            score = float(data.get("score", 1.0))
            critique = data.get("critique", "")
    except Exception as e:
        return {"score": 1.0, "critique": "", "skill_rewritten": False, "error": str(e)}

    skill_rewritten = False

    # Rewrite skill file if below threshold.
    # GUARD: by default we never overwrite the human-authored agent .md skill
    # files — doing so on every sub-threshold run is what gutted the agent
    # definitions (terse LLM "improvements" replacing rich prompts). The
    # reflexion score/critique is still logged to reflexion_log below. Opt back
    # in with ARCHONHUB_WRITE_SKILL_FILES=1.
    if score < REFLEXION_THRESHOLD and os.environ.get("ARCHONHUB_WRITE_SKILL_FILES") == "1":
        try:
            from hub_nodes import read_agent_skill_file
            current_skill, skill_path = read_agent_skill_file(agent_id)
            if current_skill and skill_path:
                rw_prompt = _REWRITE_PROMPT.format(
                    agent_id=agent_id,
                    current_skill=current_skill[:3000],
                    critique=critique,
                    score=score,
                    task=task[:400],
                    output=output[:800],
                )
                model2 = _llm(temperature=0.4)
                rw_resp = model2.invoke([HumanMessage(content=rw_prompt)])
                new_skill = rw_resp.content if hasattr(rw_resp, "content") else str(rw_resp)
                if new_skill.strip():
                    Path(skill_path).write_text(new_skill, encoding="utf-8")
                    skill_rewritten = True
        except Exception:
            pass

    # Log to DB
    try:
        now = datetime.now(timezone.utc).isoformat()
        with _conn() as c:
            c.execute("""
                INSERT INTO reflexion_log
                  (id, agent_id, run_id, task, output, score, critique, skill_rewritten, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT (id) DO UPDATE SET
                  agent_id = EXCLUDED.agent_id,
                  run_id = EXCLUDED.run_id,
                  task = EXCLUDED.task,
                  output = EXCLUDED.output,
                  score = EXCLUDED.score,
                  critique = EXCLUDED.critique,
                  skill_rewritten = EXCLUDED.skill_rewritten,
                  created_at = EXCLUDED.created_at
            """, (log_id, agent_id, run_id, task[:500], output[:1000],
                  score, critique, int(skill_rewritten), now))
    except Exception:
        pass

    return {"score": score, "critique": critique, "skill_rewritten": skill_rewritten}


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 · Conversation Memory Auto-Extraction
# ─────────────────────────────────────────────────────────────────────────────

def auto_extract_memory(user_msg: str, agent_reply: str) -> list[dict]:
    """
    After every Inez conversation turn, extract new personal facts.
    Only stores high-confidence facts not already in memory.
    Returns list of newly stored fact dicts.
    """
    # Skip very short / trivial exchanges
    if len(user_msg) < 20 or len(agent_reply) < 30:
        return []

    # Skip if purely a command or question with no personal content
    trivial_patterns = [
        r"^\s*(yes|no|ok|okay|sure|thanks?|got it|cool|great|nice)\s*[.!]?\s*$",
        r"^\s*what (is|are|does|did|do)\b",
        r"^\s*(show|list|get|fetch|run|execute)\b",
    ]
    for pat in trivial_patterns:
        if re.match(pat, user_msg.strip(), re.IGNORECASE):
            return []

    try:
        import global_memory as gm
        stored = gm.extract_and_store(user_msg, agent_reply, source="conversation")
        return stored
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 · Skill Level Progression
# ─────────────────────────────────────────────────────────────────────────────

def record_interaction(
    agent_id: str,
    task: str = "",
    output: str = "",
    success: bool = True,
    quality_score: float = 1.0,
) -> str:
    """
    Record one agent interaction. Updates skill level.
    Returns the new skill level string.
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT * FROM agent_skill_levels WHERE agent_id = ?", (agent_id,)
            ).fetchone()

            if row:
                total   = row["total_runs"] + 1
                success_n = row["successful_runs"] + (1 if success else 0)
                avg_q   = ((row["avg_quality"] * row["total_runs"]) + quality_score) / total
            else:
                total   = 1
                success_n = 1 if success else 0
                avg_q   = quality_score

            success_rate = success_n / total if total > 0 else 0.0
            level = _compute_skill_level(total, success_rate)

            c.execute("""
                INSERT INTO agent_skill_levels
                  (agent_id, total_runs, successful_runs, avg_quality, skill_level, updated_at)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT (agent_id) DO UPDATE SET
                  total_runs = EXCLUDED.total_runs,
                  successful_runs = EXCLUDED.successful_runs,
                  avg_quality = EXCLUDED.avg_quality,
                  skill_level = EXCLUDED.skill_level,
                  updated_at = EXCLUDED.updated_at
            """, (agent_id, total, success_n, avg_q, level, now))

        return level
    except Exception:
        return "novice"


def _compute_skill_level(total_runs: int, success_rate: float) -> str:
    if total_runs >= 200 and success_rate >= 0.90:
        return "master"
    if total_runs >= 50 and success_rate >= 0.80:
        return "expert"
    if total_runs >= 10 and success_rate >= 0.60:
        return "intermediate"
    return "novice"


def get_skill_level(agent_id: str) -> str:
    """Return current skill level for an agent."""
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT skill_level FROM agent_skill_levels WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()
            return row["skill_level"] if row else "novice"
    except Exception:
        return "novice"


def get_skill_stats(agent_id: str) -> dict:
    """Return full skill stats for an agent."""
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT * FROM agent_skill_levels WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            if row:
                return dict(row)
    except Exception:
        pass
    return {
        "agent_id": agent_id,
        "total_runs": 0,
        "successful_runs": 0,
        "avg_quality": 0.0,
        "skill_level": "novice",
    }


_SKILL_CONTEXT = {
    "novice": (
        "You are building experience. Focus on completing tasks accurately "
        "before optimising for speed or creativity."
    ),
    "intermediate": (
        "You have solid experience. Apply structured reasoning, consider "
        "edge cases, and produce well-organised output."
    ),
    "expert": (
        "You are highly capable. Use advanced strategies, anticipate follow-up "
        "needs, and deliver concise, high-impact responses."
    ),
    "master": (
        "You operate at master level. Apply the most sophisticated strategies "
        "available, proactively flag risks, synthesise across domains, and "
        "deliver responses that exceed expectations."
    ),
}


def inject_skill_context(agent_id: str, system_prompt: str) -> str:
    """
    Prepend a skill-level badge and behaviour directive to a system prompt.
    Called by agent_runner before every LLM invocation.
    """
    stats = get_skill_stats(agent_id)
    level = stats.get("skill_level", "novice")
    runs  = stats.get("total_runs", 0)
    rate  = (
        stats["successful_runs"] / runs
        if runs > 0 else 0.0
    )
    badge = (
        f"[SKILL: {level.upper()} | {runs} runs | "
        f"{rate*100:.0f}% success rate]\n"
        f"{_SKILL_CONTEXT[level]}\n\n"
    )
    return badge + system_prompt


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 · Pattern Detection & Proactive Actions
# ─────────────────────────────────────────────────────────────────────────────

def record_topic(
    topic: str,
    agent_id: str = "",
    user_id: str = "default",
    timestamp: str = "",
) -> None:
    """Record a topic mention. Called after every agent run or Inez message."""
    import uuid
    now = timestamp or datetime.now(timezone.utc).isoformat()
    hour = datetime.fromisoformat(now.replace("Z","")).strftime("%H:00")

    try:
        with _conn() as c:
            row = c.execute("""
                SELECT id, occurrence_count FROM interaction_patterns
                WHERE user_id=? AND topic=? AND agent_id=?
            """, (user_id, topic, agent_id)).fetchone()

            if row:
                c.execute("""
                    UPDATE interaction_patterns
                    SET occurrence_count=occurrence_count+1, last_seen=?, typical_time=?
                    WHERE id=?
                """, (now, hour, row["id"]))
            else:
                c.execute("""
                    INSERT INTO interaction_patterns
                      (id, user_id, topic, agent_id, occurrence_count, last_seen,
                       first_seen, typical_time, proactive_sent)
                    VALUES (?,?,?,?,1,?,?,?,0)
                """, (str(uuid.uuid4()), user_id, topic, agent_id, now, now, hour))
    except Exception:
        pass


def detect_patterns(user_id: str = "default") -> list[dict]:
    """
    Return patterns that:
    - Have ≥ PATTERN_MIN_OCCURRENCES occurrences
    - Were seen within PATTERN_WINDOW_DAYS
    - Haven't had a proactive brief sent yet (or have recurred since)
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=PATTERN_WINDOW_DAYS)).isoformat()
    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT * FROM interaction_patterns
                WHERE user_id=? AND occurrence_count>=? AND last_seen>=?
                ORDER BY occurrence_count DESC
            """, (user_id, PATTERN_MIN_OCCURRENCES, cutoff)).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_proactive_suggestions(user_id: str = "default") -> list[dict]:
    """
    Return actionable proactive suggestions based on detected patterns.
    Each suggestion includes: topic, agent_id, suggested_task, rationale.
    """
    patterns = detect_patterns(user_id)
    suggestions = []

    for p in patterns:
        if p.get("proactive_sent") and p["occurrence_count"] <= p.get("proactive_sent", 0) + 2:
            continue  # suppress until 2 more recurrences

        topic = p["topic"]
        agent = p.get("agent_id", "inez")
        count = p["occurrence_count"]
        time  = p.get("typical_time", "")

        suggestions.append({
            "topic": topic,
            "agent_id": agent,
            "occurrence_count": count,
            "typical_time": time,
            "suggested_task": f"Proactive briefing on: {topic}",
            "rationale": (
                f"You've asked about '{topic}' {count} times"
                + (f", usually around {time}" if time else "")
                + ". I can prepare this automatically before you ask."
            ),
        })

    return suggestions[:5]  # top 5 suggestions


def mark_proactive_sent(pattern_id: str) -> None:
    """Mark a pattern as having received a proactive brief."""
    try:
        with _conn() as c:
            c.execute("""
                UPDATE interaction_patterns
                SET proactive_sent=occurrence_count
                WHERE id=?
            """, (pattern_id,))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Combined: full post-run hook (call from agent_runner)
# ─────────────────────────────────────────────────────────────────────────────

def post_run_hook(
    agent_id: str,
    task: str,
    output: str,
    run_id: str = "",
    success: bool = True,
    user_id: str = "default",
) -> dict:
    """
    Single call to trigger all PI layers after an agent run completes.
    Call from agent_runner.run_agent() after step 8.

    Returns combined metadata for logging.
    """
    # Layer 1 — Reflexion scoring (async-friendly: runs in background)
    try:
        reflexion = reflexion_score_run(agent_id, task, output, run_id)
        quality   = reflexion.get("score", 1.0)
    except Exception:
        reflexion = {}
        quality   = 1.0

    # Layer 3 — Record interaction + update skill level
    skill_level = record_interaction(agent_id, task, output, success, quality)

    # Layer 4 — Record topic from task keywords
    _record_topics_from_text(task + " " + output[:200], agent_id, user_id)

    return {
        "reflexion_score":    reflexion.get("score"),
        "critique":           reflexion.get("critique", ""),
        "skill_rewritten":    reflexion.get("skill_rewritten", False),
        "skill_level":        skill_level,
    }


def _record_topics_from_text(text: str, agent_id: str, user_id: str):
    """Extract and record key topics from text."""
    # Simple keyword extraction — map common keywords to canonical topics
    TOPIC_KEYWORDS = {
        "market":    ["market", "nvda", "option", "trade", "stock", "invest"],
        "email":     ["email", "inbox", "gmail", "message", "reply"],
        "todo":      ["todo", "task", "checklist", "action item"],
        "grant":     ["grant", "funding", "501c3", "nonprofit"],
        "ministry":  ["sermon", "church", "soulspeak", "ministry", "preaching"],
        "wordpress": ["wordpress", "plugin", "xftc", "pbs", "woocommerce"],
        "briefing":  ["brief", "morning", "summary", "report"],
        "travel":    ["flight", "travel", "trip", "hotel"],
        "sigma":     ["sigma signal", "newsletter", "article", "content"],
    }
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            record_topic(topic, agent_id, user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Status / summary for API + iOS
# ─────────────────────────────────────────────────────────────────────────────

def get_intelligence_summary() -> dict:
    """Return a summary of the PI system state for the dashboard/iOS."""
    try:
        with _conn() as c:
            # All agent skill levels
            agents = [dict(r) for r in c.execute(
                "SELECT agent_id, skill_level, total_runs, avg_quality FROM agent_skill_levels"
                " ORDER BY total_runs DESC"
            ).fetchall()]

            # Recent reflexion log
            recent_reflexions = [dict(r) for r in c.execute(
                "SELECT agent_id, score, critique, skill_rewritten, created_at"
                " FROM reflexion_log ORDER BY created_at DESC LIMIT 10"
            ).fetchall()]

            # Top patterns
            patterns = detect_patterns()[:5]

        return {
            "agent_skill_levels": agents,
            "recent_reflexions": recent_reflexions,
            "top_patterns": patterns,
            "proactive_suggestions": get_proactive_suggestions(),
        }
    except Exception as e:
        return {"error": str(e)}
