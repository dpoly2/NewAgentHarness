"""
AgentShield — pre-dispatch prompt security scanner.
Inspired by affaan-m/ECC AgentShield (MIT).
Checks prompts for injection, exfiltration, jailbreak, and PII patterns
before dispatching to LLM.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("agent_shield")


@dataclass
class ShieldResult:
    safe: bool
    risk_level: str  # "safe", "low", "medium", "high", "critical"
    flags: list[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None


_CRITICAL_RULES: dict[str, tuple[re.Pattern[str], ...]] = {
    "prompt_injection": (
        re.compile(r"\bignore\s+(?:all\s+|any\s+|the\s+)?previous instructions\b", re.I),
        re.compile(r"\bdisregard\s+(?:your|the|all)?\s*(?:rules|instructions|guidelines)\b", re.I),
        re.compile(r"\bforget everything\b", re.I),
        re.compile(r"\bnew instructions\s*:", re.I),
        re.compile(r"\bsystem\s*:\s*you are now\b", re.I),
        re.compile(r"\boverride\s*:", re.I),
    ),
    "jailbreak_attempt": (
        re.compile(r"\bDAN\b", re.I),
        re.compile(r"\bdo anything now\b", re.I),
        re.compile(r"\bpretend you have no restrictions\b", re.I),
        re.compile(r"\bact as if you have no guidelines\b", re.I),
        re.compile(r"\bdeveloper mode\b", re.I),
        re.compile(r"\broleplay as (?:an? )?(?:unfiltered|uncensored)\b", re.I),
    ),
    "credential_exfil": (
        re.compile(r"\bshow me your\s+\.env\b", re.I),
        re.compile(r"\bwhat is your api key\b", re.I),
        re.compile(r"\bprint your credentials\b", re.I),
        re.compile(r"\b(?:show|print|reveal|dump|list|export)\b.{0,40}\b(?:api keys?|passwords?|secrets?|tokens?|credentials?)\b", re.I),
        re.compile(r"\baws secret access key\b", re.I),
    ),
}

_HIGH_RULES: dict[str, tuple[re.Pattern[str], ...]] = {
    "data_exfil": (
        re.compile(r"\bdump (?:the )?(?:database|db)\b", re.I),
        re.compile(r"\blist all users\b", re.I),
        re.compile(r"\bexport all records\b", re.I),
        re.compile(r"\bdump all (?:records|customers|clients|users)\b", re.I),
    ),
    "instruction_override": (
        re.compile(r"\byou must now\b", re.I),
        re.compile(r"\byour new task is to ignore\b", re.I),
        re.compile(r"\bfrom now on you will\b", re.I),
    ),
    "pii_request": (
        re.compile(r"\b(?:ssn|social security number)\b", re.I),
        re.compile(r"\bcredit card numbers?\b", re.I),
        re.compile(r"\b(?:full date of birth|date of birth|dob)\b.{0,40}\b(?:name|full name)\b", re.I),
        re.compile(r"\b(?:name|full name)\b.{0,40}\b(?:full date of birth|date of birth|dob)\b", re.I),
    ),
}

_SCOPE_DOMAINS: dict[str, tuple[str, tuple[re.Pattern[str], ...]]] = {
    "travel": (
        "markets",
        (
            re.compile(r"\b(?:stocks?|options?|trading|portfolio|earnings|equities)\b", re.I),
            re.compile(r"\b(?:buy|sell)\b.{0,30}\b(?:stock|shares|options?)\b", re.I),
        ),
    ),
    "market": (
        "travel",
        (
            re.compile(r"\b(?:flight|hotel|airbnb|itinerary|airport|booking)\b", re.I),
            re.compile(r"\b(?:trip|travel)\b.{0,30}\b(?:plan|book|arrange)\b", re.I),
        ),
    ),
    "finance": (
        "travel",
        (
            re.compile(r"\b(?:flight|hotel|airbnb|itinerary|airport|booking)\b", re.I),
        ),
    ),
}

_BLOCK_REASONS = {
    "prompt_injection": "prompt injection pattern detected",
    "jailbreak_attempt": "jailbreak pattern detected",
    "credential_exfil": "credential exfiltration attempt detected",
}


def _matches(text: str, rules: dict[str, tuple[re.Pattern[str], ...]]) -> list[str]:
    flags: list[str] = []
    for flag, patterns in rules.items():
        if any(pattern.search(text) for pattern in patterns):
            flags.append(flag)
    return flags


def _scope_violation_flag(text: str, agent_id: str) -> list[str]:
    agent_key = (agent_id or "").strip().lower()
    if not agent_key:
        return []
    for domain_key, (_, patterns) in _SCOPE_DOMAINS.items():
        if domain_key in agent_key and any(pattern.search(text) for pattern in patterns):
            return ["scope_violation"]
    return []


def _sensitive_topic_flag(text: str) -> list[str]:
    investment_action = re.search(r"\b(?:buy|sell)\b.{0,30}\b(?:stock|shares|options?)\b", text, re.I)
    external_audience = re.search(
        r"\b(?:tell|recommend to|advise)\b.{0,30}\b(?:clients?|customers?|subscribers?|the public)\b",
        text,
        re.I,
    )
    return ["sensitive_topic"] if investment_action and external_audience else []


def scan_prompt(prompt: str, agent_id: str = "") -> ShieldResult:
    """Scan a prompt for security risks before dispatching to LLM."""
    text = (prompt or "").strip()
    if not text:
        return ShieldResult(safe=True, risk_level="safe")

    critical_flags = _matches(text, _CRITICAL_RULES)
    high_flags = _matches(text, _HIGH_RULES)
    medium_flags = _sensitive_topic_flag(text) + _scope_violation_flag(text, agent_id)

    if critical_flags:
        blocked = "; ".join(_BLOCK_REASONS.get(flag, flag) for flag in critical_flags)
        return ShieldResult(
            safe=False,
            risk_level="critical",
            flags=critical_flags,
            blocked_reason=blocked,
        )
    if high_flags:
        return ShieldResult(safe=True, risk_level="high", flags=high_flags)
    if medium_flags:
        return ShieldResult(safe=True, risk_level="medium", flags=medium_flags)
    return ShieldResult(safe=True, risk_level="safe")


def _insert_todo_with_conn(conn: sqlite3.Connection, title: str, description: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO todos (
            id, title, description, priority, status, project,
            due_date, tags, source, created_at, updated_at
        )
        VALUES (?, ?, ?, 'high', 'pending', 'devops', '', '[]', 'agent_shield', ?, ?)
        """,
        (str(uuid.uuid4()), title, description, now, now),
    )


def scan_task_and_log(task: str, agent_id: str, db=None) -> ShieldResult:
    """Scan task + log HIGH/CRITICAL detections as DevOps todos in the DB."""
    result = scan_prompt(task, agent_id=agent_id)
    if result.risk_level not in {"high", "critical"} or db is None:
        return result

    preview = (task or "").replace("\r", " ").replace("\n", " ")[:200]
    description = f"Flags: {', '.join(result.flags)}. Task preview: {preview}"
    title = f"[AgentShield] {result.risk_level.upper()} in {agent_id}"

    try:
        if hasattr(db, "create_todo"):
            db.create_todo(
                title=title,
                description=description,
                project="devops",
                priority="high",
                source="agent_shield",
            )
        elif hasattr(db, "get_conn"):
            with db.get_conn() as conn:
                _insert_todo_with_conn(conn, title, description)
        elif hasattr(db, "execute"):
            _insert_todo_with_conn(db, title, description)
            db.commit()
    except Exception as exc:
        logger.debug("AgentShield todo logging failed: %s", exc)

    return result
