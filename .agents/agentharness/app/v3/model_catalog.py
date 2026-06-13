"""
model_catalog.py — ArchonHub Model Catalog
==========================================
Central registry of every LLM provider and model supported by ArchonHub.

Features:
  • Canonical list of providers (OpenAI, Anthropic, Gemini, Groq, Ollama, GitHub Models, Perplexity)
  • Each model tagged with capability labels used for intelligent routing
  • Enable/disable per model stored in hub_config DB
  • Perplexity-style auto-routing: given a task type, pick the best enabled model
  • API key validation (checks env var, not stored in DB)

Routing logic (mirrors Perplexity's model selection approach):
  Priority 1 — task_type maps to a "best model" per capability
  Priority 2 — fallback to the globally configured llm_model
  Priority 3 — any enabled model in the provider

Capability tags:
  "reasoning"    — complex multi-step logic, chains of thought
  "code"         — code generation, review, debugging
  "fast"         — low latency, simple tasks, classification
  "long_context" — >64k tokens, document analysis
  "vision"       — image understanding
  "search"       — web-grounded responses (Perplexity)
  "finance"      — financial data reasoning
  "writing"      — creative and professional writing
  "agents"       — agentic task completion, tool use
"""
from __future__ import annotations

import os
from typing import Any

# ── Canonical model catalog ───────────────────────────────────────────────────
# Each entry: provider, model_id, display_name, capabilities[], context_k, notes
CATALOG: list[dict[str, Any]] = [

    # ── OpenAI ────────────────────────────────────────────────────────────────
    {"provider": "openai", "model_id": "gpt-4.1",           "display": "GPT-4.1",            "capabilities": ["reasoning", "code", "agents", "writing", "long_context"], "context_k": 1047, "tier": "premium"},
    {"provider": "openai", "model_id": "gpt-4o",            "display": "GPT-4o",              "capabilities": ["reasoning", "code", "vision", "agents", "writing"],       "context_k": 128,  "tier": "premium"},
    {"provider": "openai", "model_id": "gpt-4o-mini",       "display": "GPT-4o Mini",         "capabilities": ["fast", "code", "writing", "agents"],                      "context_k": 128,  "tier": "standard"},
    {"provider": "openai", "model_id": "o3",                "display": "o3",                  "capabilities": ["reasoning", "code", "agents"],                            "context_k": 200,  "tier": "premium"},
    {"provider": "openai", "model_id": "o4-mini",           "display": "o4-mini",             "capabilities": ["reasoning", "code", "fast"],                              "context_k": 128,  "tier": "standard"},
    {"provider": "openai", "model_id": "gpt-3.5-turbo",     "display": "GPT-3.5 Turbo",       "capabilities": ["fast", "writing"],                                        "context_k": 16,   "tier": "economy"},

    # ── Anthropic ─────────────────────────────────────────────────────────────
    {"provider": "anthropic", "model_id": "claude-opus-4-5",    "display": "Claude Opus 4.5",     "capabilities": ["reasoning", "code", "agents", "writing", "long_context"], "context_k": 200, "tier": "premium"},
    {"provider": "anthropic", "model_id": "claude-sonnet-4-5",  "display": "Claude Sonnet 4.5",   "capabilities": ["reasoning", "code", "agents", "writing"],                 "context_k": 200, "tier": "standard"},
    {"provider": "anthropic", "model_id": "claude-haiku-4-5",   "display": "Claude Haiku 4.5",    "capabilities": ["fast", "writing", "code"],                                "context_k": 200, "tier": "economy"},
    {"provider": "anthropic", "model_id": "claude-3-5-sonnet-20241022", "display": "Claude 3.5 Sonnet", "capabilities": ["reasoning", "code", "vision", "agents", "writing"], "context_k": 200, "tier": "standard"},

    # ── Google Gemini ─────────────────────────────────────────────────────────
    {"provider": "gemini", "model_id": "gemini-2.5-pro",    "display": "Gemini 2.5 Pro",      "capabilities": ["reasoning", "code", "vision", "agents", "long_context"],   "context_k": 1000, "tier": "premium"},
    {"provider": "gemini", "model_id": "gemini-2.5-flash",  "display": "Gemini 2.5 Flash",    "capabilities": ["fast", "code", "vision", "writing"],                       "context_k": 1000, "tier": "standard"},
    {"provider": "gemini", "model_id": "gemini-1.5-pro",    "display": "Gemini 1.5 Pro",      "capabilities": ["reasoning", "vision", "long_context", "writing"],          "context_k": 2000, "tier": "standard"},
    {"provider": "gemini", "model_id": "gemini-1.5-flash",  "display": "Gemini 1.5 Flash",    "capabilities": ["fast", "writing", "vision"],                               "context_k": 1000, "tier": "economy"},

    # ── Groq (fast inference) ─────────────────────────────────────────────────
    {"provider": "groq", "model_id": "llama-3.3-70b-versatile",   "display": "Llama 3.3 70B (Groq)",  "capabilities": ["reasoning", "code", "agents", "fast"],  "context_k": 128,  "tier": "standard"},
    {"provider": "groq", "model_id": "llama-3.1-8b-instant",      "display": "Llama 3.1 8B (Groq)",   "capabilities": ["fast", "writing"],                       "context_k": 128,  "tier": "economy"},
    {"provider": "groq", "model_id": "mixtral-8x7b-32768",        "display": "Mixtral 8x7B (Groq)",   "capabilities": ["reasoning", "code", "writing"],          "context_k": 32,   "tier": "standard"},
    {"provider": "groq", "model_id": "gemma2-9b-it",              "display": "Gemma2 9B (Groq)",      "capabilities": ["fast", "writing", "code"],               "context_k": 8,    "tier": "economy"},

    # ── Perplexity ────────────────────────────────────────────────────────────
    {"provider": "perplexity", "model_id": "sonar-pro",           "display": "Sonar Pro",             "capabilities": ["search", "reasoning", "writing"],        "context_k": 200,  "tier": "premium"},
    {"provider": "perplexity", "model_id": "sonar",               "display": "Sonar",                 "capabilities": ["search", "fast", "writing"],             "context_k": 128,  "tier": "standard"},
    {"provider": "perplexity", "model_id": "sonar-reasoning-pro", "display": "Sonar Reasoning Pro",   "capabilities": ["search", "reasoning", "finance"],        "context_k": 128,  "tier": "premium"},
    {"provider": "perplexity", "model_id": "sonar-reasoning",     "display": "Sonar Reasoning",       "capabilities": ["search", "reasoning"],                   "context_k": 128,  "tier": "standard"},

    # ── GitHub Models (Azure inference) ───────────────────────────────────────
    {"provider": "github", "model_id": "gpt-4o",             "display": "GPT-4o (GitHub)",    "capabilities": ["reasoning", "code", "vision", "agents"],         "context_k": 128,  "tier": "standard"},
    {"provider": "github", "model_id": "Meta-Llama-3.1-70B-Instruct", "display": "Llama 3.1 70B (GitHub)", "capabilities": ["reasoning", "code", "agents"], "context_k": 128, "tier": "standard"},
    {"provider": "github", "model_id": "Mistral-large",      "display": "Mistral Large (GitHub)", "capabilities": ["reasoning", "code", "writing"],             "context_k": 128,  "tier": "standard"},

    # ── Ollama (local) ────────────────────────────────────────────────────────
    # Ollama models are dynamically discovered; these are common ones shown in UI
    {"provider": "ollama", "model_id": "llama3.1",           "display": "Llama 3.1 (local)",  "capabilities": ["reasoning", "agents", "writing"],                "context_k": 128,  "tier": "local"},
    {"provider": "ollama", "model_id": "llama3.2",           "display": "Llama 3.2 (local)",  "capabilities": ["fast", "writing"],                               "context_k": 128,  "tier": "local"},
    {"provider": "ollama", "model_id": "codellama",          "display": "CodeLlama (local)",  "capabilities": ["code"],                                          "context_k": 16,   "tier": "local"},
    {"provider": "ollama", "model_id": "mistral",            "display": "Mistral (local)",    "capabilities": ["reasoning", "writing"],                          "context_k": 32,   "tier": "local"},
    {"provider": "ollama", "model_id": "mixtral",            "display": "Mixtral (local)",    "capabilities": ["reasoning", "code", "writing"],                  "context_k": 32,   "tier": "local"},
    {"provider": "ollama", "model_id": "phi3",               "display": "Phi-3 (local)",      "capabilities": ["fast", "writing", "code"],                       "context_k": 128,  "tier": "local"},
    {"provider": "ollama", "model_id": "gemma2",             "display": "Gemma2 (local)",     "capabilities": ["fast", "writing"],                               "context_k": 8,    "tier": "local"},
    {"provider": "ollama", "model_id": "qwen2.5-coder",      "display": "Qwen 2.5 Coder (local)", "capabilities": ["code"],                                     "context_k": 128,  "tier": "local"},
    {"provider": "ollama", "model_id": "llava",              "display": "LLaVA (local)",      "capabilities": ["vision"],                                        "context_k": 4,    "tier": "local"},
]

# ── Capability → best model routing table ─────────────────────────────────────
# Perplexity-style: for each task type, prefer these models in order.
# The router picks the first one that is enabled AND has a valid API key.

CAPABILITY_ROUTING: dict[str, list[tuple[str, str]]] = {
    # (provider, model_id) in priority order
    "reasoning": [
        ("openai",     "o3"),
        ("anthropic",  "claude-opus-4-5"),
        ("openai",     "gpt-4.1"),
        ("gemini",     "gemini-2.5-pro"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("openai",     "gpt-4o"),
        ("anthropic",  "claude-sonnet-4-5"),
    ],
    "code": [
        ("openai",     "gpt-4.1"),
        ("anthropic",  "claude-sonnet-4-5"),
        ("openai",     "o4-mini"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("openai",     "gpt-4o"),
        ("ollama",     "codellama"),
        ("ollama",     "qwen2.5-coder"),
    ],
    "fast": [
        ("groq",       "llama-3.1-8b-instant"),
        ("openai",     "gpt-4o-mini"),
        ("anthropic",  "claude-haiku-4-5"),
        ("gemini",     "gemini-2.5-flash"),
        ("groq",       "gemma2-9b-it"),
        ("ollama",     "phi3"),
    ],
    "long_context": [
        ("gemini",     "gemini-1.5-pro"),
        ("gemini",     "gemini-2.5-pro"),
        ("anthropic",  "claude-opus-4-5"),
        ("openai",     "gpt-4.1"),
    ],
    "vision": [
        ("openai",     "gpt-4o"),
        ("gemini",     "gemini-2.5-pro"),
        ("anthropic",  "claude-3-5-sonnet-20241022"),
        ("ollama",     "llava"),
    ],
    "search": [
        ("perplexity", "sonar-pro"),
        ("perplexity", "sonar-reasoning-pro"),
        ("perplexity", "sonar"),
        ("perplexity", "sonar-reasoning"),
    ],
    "finance": [
        ("perplexity", "sonar-reasoning-pro"),
        ("openai",     "gpt-4.1"),
        ("anthropic",  "claude-opus-4-5"),
        ("groq",       "llama-3.3-70b-versatile"),
    ],
    "writing": [
        ("anthropic",  "claude-sonnet-4-5"),
        ("openai",     "gpt-4o"),
        ("openai",     "gpt-4o-mini"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("ollama",     "mistral"),
    ],
    "agents": [
        ("openai",     "gpt-4.1"),
        ("anthropic",  "claude-opus-4-5"),
        ("openai",     "gpt-4o"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("github",     "gpt-4o"),
    ],
}

# Task-type keyword → capability mapping (for agent_id and skill text routing)
TASK_CAPABILITY_MAP: dict[str, str] = {
    # code / dev
    "code": "code", "developer": "code", "engineer": "code",
    "programmer": "code", "coder": "code", "devops": "code",
    # reasoning / analysis
    "analyst": "reasoning", "researcher": "reasoning", "strategist": "reasoning",
    "planner": "reasoning", "advisor": "reasoning", "consultant": "reasoning",
    # fast / simple
    "assistant": "fast", "reviewer": "fast", "classifier": "fast",
    "summarizer": "fast", "triage": "fast",
    # writing
    "writer": "writing", "editor": "writing", "content": "writing",
    "copywriter": "writing", "journalist": "writing",
    # finance
    "finance": "finance", "markets": "finance", "trading": "finance",
    "equity": "finance", "portfolio": "finance", "cfo": "finance",
    # search / web
    "search": "search", "research": "search", "news": "search",
    # vision
    "vision": "vision", "image": "vision", "photo": "vision",
    # agents
    "agent": "agents", "lead": "agents", "manager": "agents",
    "operations": "agents", "orchestrator": "agents",
}

# ── Provider env-var map ──────────────────────────────────────────────────────
PROVIDER_ENV_KEYS: dict[str, str] = {
    "openai":      "OPENAI_API_KEY",
    "anthropic":   "ANTHROPIC_API_KEY",
    "gemini":      "GEMINI_API_KEY",
    "groq":        "GROQ_API_KEY",
    "perplexity":  "PERPLEXITY_API_KEY",
    "github":      "GITHUB_TOKEN",
    "ollama":      "",          # no key needed
}

PROVIDER_BASE_URLS: dict[str, str] = {
    "groq":        "https://api.groq.com/openai/v1",
    "perplexity":  "https://api.perplexity.ai",
    "github":      "https://models.inference.ai.azure.com",
    "ollama":      "http://localhost:11434/v1",
}


def provider_has_key(provider: str) -> bool:
    """True if the provider's API key is configured in env."""
    env_key = PROVIDER_ENV_KEYS.get(provider, "")
    if not env_key:
        return provider == "ollama"  # ollama needs no key
    return bool(os.environ.get(env_key, "").strip())


def get_catalog() -> list[dict]:
    """Return full catalog with dynamic fields: key_configured, enabled (from DB)."""
    from hub_db import get_conn
    # Load enabled states from DB
    enabled_map: dict[str, bool] = {}
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM hub_config WHERE key LIKE 'model_enabled_%'"
            ).fetchall()
            for row in rows:
                k = row["key"].removeprefix("model_enabled_")
                enabled_map[k] = row["value"] not in ("false", "0", "False", "null")
    except Exception:
        pass

    result = []
    for entry in CATALOG:
        key = f"{entry['provider']}__{entry['model_id']}"
        has_key = provider_has_key(entry["provider"])
        # Default: enabled if provider has API key configured
        enabled = enabled_map.get(key, has_key)
        result.append({
            **entry,
            "key":            key,
            "key_configured": has_key,
            "enabled":        enabled,
        })
    return result


def set_model_enabled(provider: str, model_id: str, enabled: bool) -> None:
    """Persist enable/disable for a model in hub_config."""
    from hub_db import get_conn
    import json as _json
    from datetime import datetime, timezone
    key = f"model_enabled_{provider}__{model_id}"
    val = _json.dumps(enabled)
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO hub_config (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, val, now)
        )


def route_for_task(task_type: str, agent_id: str = "") -> dict | None:
    """
    Perplexity-style routing: given a task type or agent_id, return the best
    available enabled model as {"provider", "model_id", "display", "reason"}.

    Returns None if no suitable model is available.
    """
    # Determine capability from task_type or agent_id
    capability = TASK_CAPABILITY_MAP.get(task_type.lower())
    if not capability:
        # Try to infer from agent_id tokens
        for token in agent_id.lower().replace("_", "-").split("-"):
            if token in TASK_CAPABILITY_MAP:
                capability = TASK_CAPABILITY_MAP[token]
                break

    # Build enabled model set
    catalog = get_catalog()
    enabled_set = {(m["provider"], m["model_id"]) for m in catalog if m["enabled"]}

    # Walk capability routing table
    candidates = CAPABILITY_ROUTING.get(capability or "reasoning", [])
    for provider, model_id in candidates:
        if (provider, model_id) in enabled_set and provider_has_key(provider):
            entry = next((m for m in CATALOG if m["provider"] == provider and m["model_id"] == model_id), None)
            return {
                "provider":  provider,
                "model_id":  model_id,
                "display":   entry["display"] if entry else model_id,
                "capability": capability or "reasoning",
                "reason":    f"Best enabled model for '{capability or 'reasoning'}' task",
            }

    # Fallback: any enabled model with a key
    for m in catalog:
        if m["enabled"] and m["key_configured"]:
            return {
                "provider":  m["provider"],
                "model_id":  m["model_id"],
                "display":   m["display"],
                "capability": "fallback",
                "reason":    "Fallback: first enabled model with API key",
            }
    return None


def build_llm_from_route(route: dict, temperature: float = 0.2):
    """Build a LangChain LLM from a route() result dict."""
    provider  = route["provider"]
    model_id  = route["model_id"]
    env_key   = PROVIDER_ENV_KEYS.get(provider, "")
    api_key   = os.environ.get(env_key, "sk-placeholder") if env_key else "ollama"
    base_url  = PROVIDER_BASE_URLS.get(provider, "")

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
            return ChatAnthropic(model=model_id, temperature=temperature, api_key=api_key)
        except ImportError:
            pass

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
            return ChatGoogleGenerativeAI(model=model_id, temperature=temperature, google_api_key=api_key)
        except ImportError:
            pass

    from langchain_openai import ChatOpenAI  # type: ignore
    kwargs: dict = {"model": model_id, "temperature": temperature, "api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)
