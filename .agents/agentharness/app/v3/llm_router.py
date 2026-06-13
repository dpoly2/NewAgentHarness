"""
llm_router.py — ArchonHub Dynamic LLM Router
=============================================
Provides intelligent model routing:
  • Auto-discovers available Ollama models from localhost:11434
  • Maps skill types to best available model (Ollama-first, cloud fallback)
  • Supports per-agent model overrides stored in agent_registry.config
  • Caches Ollama model list for 5 minutes to avoid repeated API calls
  • Builds LangChain LLM instances with correct provider/base_url settings

Usage:
    from llm_router import get_llm_for_agent, discover_ollama_models, SKILL_MODEL_MAP

    model = get_llm_for_agent("markets-equity-analyst", temperature=0.3)
    models = discover_ollama_models()   # [{"name": "llama3.2", "size_gb": 4.1, ...}]
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

import sys
HERE = Path(__file__).parent
for _p in [HERE, HERE.parent.parent, HERE.parent.parent.parent]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from ah_logging import get_logger
    logger = get_logger("llm_router")
except Exception:
    import logging
    logger = logging.getLogger("llm_router")

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_BASE    = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_BASE}/api/tags"
OLLAMA_V1_URL  = f"{OLLAMA_BASE}/v1"

_ollama_cache: list[dict] = []
_ollama_cache_ts: float = 0.0
_CACHE_TTL = 300  # 5 minutes


def discover_ollama_models(force_refresh: bool = False) -> list[dict]:
    """
    Query Ollama /api/tags. Returns list of model dicts:
        {"name": "llama3.2:latest", "display": "llama3.2", "size_gb": 4.1,
         "family": "llama", "params": "3.2B", "available": True}
    Returns [] if Ollama is not running.
    """
    global _ollama_cache, _ollama_cache_ts
    if not force_refresh and _ollama_cache and (time.time() - _ollama_cache_ts) < _CACHE_TTL:
        return _ollama_cache
    try:
        req = urllib.request.Request(OLLAMA_API_URL,
                                     headers={"User-Agent": "ArchonHub/1.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
        models = []
        for m in data.get("models", []):
            name     = m.get("name", "")
            details  = m.get("details", {})
            size_b   = m.get("size", 0)
            size_gb  = round(size_b / 1e9, 1) if size_b else 0
            family   = details.get("family", "")
            param_sz = details.get("parameter_size", "")
            display  = name.split(":")[0]
            models.append({
                "name":       name,
                "display":    display,
                "size_gb":    size_gb,
                "family":     family.lower(),
                "params":     param_sz,
                "available":  True,
                "modified_at": m.get("modified_at", ""),
            })
        _ollama_cache    = models
        _ollama_cache_ts = time.time()
        logger.info("Ollama: %d model(s) available", len(models))
        return models
    except Exception as exc:
        logger.debug("Ollama not available: %s", exc)
        _ollama_cache    = []
        _ollama_cache_ts = time.time()
        return []


def ollama_is_running() -> bool:
    return len(discover_ollama_models()) > 0


def get_ollama_model_names() -> list[str]:
    """Returns short display names: ['llama3.2', 'mistral', 'codellama']"""
    return [m["display"] for m in discover_ollama_models()]


# ── Skill → model preference map ─────────────────────────────────────────────
# Maps skill type keywords → ordered list of preferred Ollama model name fragments.
# First match wins. If none match, falls back to global config model.
SKILL_MODEL_MAP: dict[str, list[str]] = {
    # Code-heavy agents
    "code":        ["codellama", "qwen2.5-coder", "deepseek-coder", "starcoder", "codegemma", "llama3.1", "llama3.2", "mistral"],
    "developer":   ["codellama", "qwen2.5-coder", "deepseek-coder", "llama3.1", "llama3.2"],
    "engineer":    ["codellama", "qwen2.5-coder", "deepseek-coder", "llama3.1", "mistral"],
    # Analysis / research
    "analyst":     ["llama3.1", "llama3.2", "mistral", "mixtral", "gemma2", "phi3"],
    "researcher":  ["llama3.1", "mistral", "mixtral", "llama3.2", "gemma2"],
    "strategist":  ["llama3.1", "mixtral", "mistral", "llama3.2", "gemma2"],
    "planner":     ["llama3.1", "mixtral", "mistral", "llama3.2"],
    # Writing / comms
    "writer":      ["llama3.2", "mistral", "llama3.1", "gemma2", "phi3"],
    "editor":      ["llama3.2", "mistral", "llama3.1", "gemma2"],
    "content":     ["llama3.2", "mistral", "llama3.1"],
    # Markets / finance
    "markets":     ["llama3.1", "mixtral", "mistral", "llama3.2"],
    "portfolio":   ["llama3.1", "mixtral", "mistral"],
    "trading":     ["llama3.1", "mixtral", "mistral"],
    "equity":      ["llama3.1", "mixtral", "mistral"],
    # Operations / management
    "operations":  ["llama3.2", "mistral", "phi3", "llama3.1"],
    "lead":        ["llama3.1", "llama3.2", "mistral", "mixtral"],
    "manager":     ["llama3.1", "llama3.2", "mistral"],
    # Small / fast for simple tasks
    "assistant":   ["phi3", "llama3.2", "gemma2", "mistral"],
    "reviewer":    ["llama3.2", "mistral", "phi3", "llama3.1"],
    # Multimodal / vision
    "vision":      ["llava", "moondream", "llama3.2-vision"],
    "image":       ["llava", "moondream", "llama3.2-vision"],
}

# Fallback priority when no skill match: prefer capable general models
_GENERAL_PRIORITY = ["llama3.1", "llama3.2", "mistral", "mixtral", "gemma2", "phi3", "qwen2.5"]


def _match_ollama_model(preferences: list[str], available: list[str]) -> str | None:
    """
    Given ordered preference list and available Ollama model names,
    return best match or None.
    """
    avail_lower = [a.lower() for a in available]
    for pref in preferences:
        pref_l = pref.lower()
        for i, a in enumerate(avail_lower):
            if pref_l in a:
                return available[i]
    return None


def get_best_model_for_skill(skill_keywords: list[str]) -> tuple[str, str] | None:
    """
    Returns (model_name, provider) for the best available Ollama model
    given a list of skill keywords extracted from the agent ID or skill text.
    Returns None if Ollama is not running.
    """
    available = get_ollama_model_names()
    if not available:
        return None

    # Try each keyword in priority order
    for kw in skill_keywords:
        kw_l = kw.lower()
        prefs = SKILL_MODEL_MAP.get(kw_l, [])
        match = _match_ollama_model(prefs, available)
        if match:
            return (match, "ollama")

    # General fallback to best available
    match = _match_ollama_model(_GENERAL_PRIORITY, available)
    if match:
        return (match, "ollama")

    # Any available model
    return (available[0], "ollama")


def extract_skill_keywords(agent_id: str, skill_text: str = "") -> list[str]:
    """
    Extract skill type keywords from agent_id and optional skill text.
    e.g. "markets-equity-analyst" → ["markets", "equity", "analyst"]
    """
    kws = [p.lower() for p in agent_id.replace("_", "-").split("-") if len(p) > 2]
    # Also scan first 500 chars of skill text for role keywords
    if skill_text:
        text_lower = skill_text[:500].lower()
        for kw in SKILL_MODEL_MAP:
            if kw in text_lower and kw not in kws:
                kws.append(kw)
    return kws


# ── Per-agent model override ──────────────────────────────────────────────────

def get_agent_model_override(agent_id: str) -> dict | None:
    """
    Returns {"provider": ..., "model": ..., "base_url": ...} if the agent
    has a preferred model stored in agent_registry.config, else None.
    """
    try:
        import hub_db
        agent = hub_db.get_agent(agent_id)
        if not agent:
            return None
        config = agent.get("config") or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except Exception:
                return None
        prov  = config.get("preferred_provider", "")
        model = config.get("preferred_model", "")
        if prov and model:
            return {"provider": prov, "model": model,
                    "base_url": config.get("preferred_base_url", "")}
    except Exception as e:
        logger.debug("get_agent_model_override failed: %s", e)
    return None


def set_agent_model_override(agent_id: str, provider: str, model: str,
                              base_url: str = "") -> bool:
    """Persist preferred model to agent_registry.config."""
    try:
        import hub_db
        agent = hub_db.get_agent(agent_id)
        if not agent:
            return False
        config = agent.get("config") or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except Exception:
                config = {}
        config["preferred_provider"] = provider
        config["preferred_model"]    = model
        config["preferred_base_url"] = base_url
        hub_db.update_agent(agent_id, config=config)
        return True
    except Exception as e:
        logger.error("set_agent_model_override failed: %s", e)
        return False


def clear_agent_model_override(agent_id: str) -> bool:
    """Remove model override — agent will use global config."""
    try:
        import hub_db
        agent = hub_db.get_agent(agent_id)
        if not agent:
            return False
        config = agent.get("config") or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except Exception:
                config = {}
        config.pop("preferred_provider", None)
        config.pop("preferred_model", None)
        config.pop("preferred_base_url", None)
        hub_db.update_agent(agent_id, config=config)
        return True
    except Exception as e:
        logger.error("clear_agent_model_override failed: %s", e)
        return False


# ── LLM builder ──────────────────────────────────────────────────────────────

_BASE_URLS: dict[str, str] = {
    "ollama":  OLLAMA_V1_URL,
    "github":  "https://models.inference.ai.azure.com",
    "groq":    "https://api.groq.com/openai/v1",
}


def build_llm(provider: str, model: str, base_url: str = "",
              api_key: str = "", temperature: float = 0.2):
    """
    Build a LangChain LLM instance for the given provider/model.
    Raises ImportError if langchain_openai is not installed.
    """
    from langchain_openai import ChatOpenAI  # type: ignore

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
            return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        except ImportError:
            pass

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
            return ChatGoogleGenerativeAI(model=model, temperature=temperature,
                                          google_api_key=api_key)
        except ImportError:
            pass

    resolved_url = base_url or _BASE_URLS.get(provider, "")
    resolved_key = api_key or (
        "ollama" if provider == "ollama" else
        os.environ.get("GITHUB_TOKEN", "") if provider == "github" else
        os.environ.get("OPENAI_API_KEY", "") or "sk-placeholder"
    )
    kwargs: dict[str, Any] = {
        "model":       model,
        "temperature": temperature,
        "api_key":     resolved_key or "sk-placeholder",
    }
    if resolved_url:
        kwargs["base_url"] = resolved_url
    return ChatOpenAI(**kwargs)


# ── Main entry point ──────────────────────────────────────────────────────────

def get_llm_for_agent(agent_id: str, skill_text: str = "",
                      temperature: float = 0.2, allow_ollama: bool = True):
    """
    Returns the best LangChain LLM for the given agent.

    Priority:
      1. Agent's stored model override (preferred_provider / preferred_model)
      2. model_catalog smart routing (Perplexity-style, uses capability tags)
      3. Ollama auto-assignment based on skill keywords (if Ollama is running)
      4. Global config from hub_db / ai_config.json / env vars (existing _llm())

    Falls back to global _llm() on any error.
    """
    # 1. Per-agent override
    override = get_agent_model_override(agent_id)
    if override:
        try:
            logger.debug("Agent %s using override: %s/%s",
                         agent_id, override["provider"], override["model"])
            return build_llm(
                provider=override["provider"],
                model=override["model"],
                base_url=override.get("base_url", ""),
                temperature=temperature,
            )
        except Exception as e:
            logger.warning("Agent override LLM failed (%s), falling back: %s", agent_id, e)

    # 2. model_catalog smart routing
    try:
        from model_catalog import route_for_task, build_llm_from_route, TASK_CAPABILITY_MAP
        kws = extract_skill_keywords(agent_id, skill_text)
        task_type = next((kw for kw in kws if kw in TASK_CAPABILITY_MAP), kws[0] if kws else "reasoning")
        route = route_for_task(task_type, agent_id)
        if route:
            llm = build_llm_from_route(route, temperature=temperature)
            logger.debug("Agent %s catalog-routed to %s/%s (%s)",
                         agent_id, route["provider"], route["model_id"], route["reason"])
            return llm
    except Exception as e:
        logger.debug("model_catalog routing failed for %s: %s", agent_id, e)

    # 3. Ollama auto-assignment
    if allow_ollama and ollama_is_running():
        kws = extract_skill_keywords(agent_id, skill_text)
        result = get_best_model_for_skill(kws)
        if result:
            model_name, provider = result
            try:
                logger.debug("Agent %s auto-assigned Ollama model: %s", agent_id, model_name)
                return build_llm(provider="ollama", model=model_name,
                                 temperature=temperature)
            except Exception as e:
                logger.warning("Ollama LLM failed (%s), falling back: %s", agent_id, e)

    # 4. Global config fallback
    try:
        from hub_nodes import _llm
        return _llm(temperature=temperature)
    except Exception as e:
        logger.error("Global _llm() fallback failed: %s", e)
        raise


def get_routing_summary(agent_ids: list[str] | None = None) -> list[dict]:
    """
    Returns current routing plan for agents — useful for the admin UI.
    Shows which model each agent would use and why.
    """
    import hub_db
    agents = hub_db.list_agents() if not agent_ids else [
        hub_db.get_agent(aid) for aid in agent_ids if hub_db.get_agent(aid)
    ]
    ollama_models = get_ollama_model_names()
    ollama_running = bool(ollama_models)

    summary = []
    for agent in agents:
        aid   = agent.get("agent_id", "")
        kws   = extract_skill_keywords(aid)
        override = get_agent_model_override(aid)

        if override:
            source = "override"
            provider = override["provider"]
            model    = override["model"]
        elif ollama_running:
            result = get_best_model_for_skill(kws)
            if result:
                source   = "ollama_auto"
                model, provider = result
            else:
                source   = "global"
                provider = "?"
                model    = "?"
        else:
            source   = "global"
            provider = "openai"
            model    = "gpt-4o-mini"

        summary.append({
            "agent_id":    aid,
            "name":        agent.get("name", aid),
            "project":     agent.get("project_slug", ""),
            "source":      source,
            "provider":    provider,
            "model":       model,
            "skill_kws":   kws,
            "has_override": bool(override),
        })
    return summary
