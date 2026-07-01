"""
gateway.py — ArchonHub unified LLM Gateway (Feature 2 of the architecture rebuild)
==================================================================================
One entry point for every LLM call, replacing the three divergent factories
(`hub_nodes._llm`, `llm_router.get_llm_for_agent`, `inez_agent._llm`).

Design (see docs/ARCHITECTURE-REBUILD.md §6 and §8.1):

  gateway.complete(task_type, messages, *, json=False, temperature=None, max_tokens=None)
      1. policy = ROUTING[task_type]            # tier + ordered fallback chain
      2. for provider in policy.chain:
             if breaker_open(provider): continue
             try:   return build(provider).invoke(messages)
             except AuthError:  trip(provider, 6h)   # dead key
             except Timeout/5xx: trip(provider, 2m)  # transient
      3. raise AllProvidersDown

Provider identifiers in a chain look like:
    "openai:gpt-4o-mini"   → provider=openai, key from hub_config['llm_key_openai']
    "local:mistral"        → provider=ollama, base_url http://localhost:11434/v1
    "local:llama3.2:1b"    → provider=ollama, model "llama3.2:1b"

Circuit-breaker state lives in `hub_config` (key `breaker_<provider>` =
JSON {"open_until": iso}) so it is SHARED across the 5 uvicorn worker
processes — one worker tripping a dead key protects the others immediately.
`free_llm_keys.note_free_call_failure` is the seed of this idea and is still
called so the free-key subsystem stays in sync.

The low-level model construction is delegated to the already-hardened
`llm_router.build_llm` (timeout, max_tokens, max_retries=0).

Everything here is wrapped defensively; logging never raises.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
for _p in (HERE, HERE.parent.parent, HERE.parent.parent.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from ah_logging import get_logger
    logger = get_logger("gateway")
except Exception:  # pragma: no cover - logging must never break the gateway
    import logging
    logger = logging.getLogger("gateway")


# ── Routing table ──────────────────────────────────────────────────────────────
# Declarative policy per task_type: an ordered provider fallback chain plus the
# defaults for json mode / temperature / token cap. Matches §8.1 of the doc, with
# the ad-hoc under-fire fixes (devops→gpt-4o-mini, Inez→gpt-4o-mini, 1b fast
# fallback) folded in as rows instead of scattered branches.
class Tier:
    __slots__ = ("chain", "json", "temperature", "max_tokens")

    def __init__(self, chain: list[str], *, json: bool = False,
                 temperature: float = 0.2, max_tokens: int = 1024):
        self.chain = chain
        self.json = json
        self.temperature = temperature
        self.max_tokens = max_tokens


ROUTING: dict[str, Tier] = {
    # Tiny/fast deterministic classification — local only, cheap.
    "classify":   Tier(chain=["local:llama3.2:1b"],
                       max_tokens=64, temperature=0.0),
    # Scoring / JSON verdicts — capable cloud first, local fallback, JSON forced.
    "evaluate":   Tier(chain=["openai:gpt-4o-mini", "local:mistral"],
                       json=True, max_tokens=256, temperature=0.0),
    # Main reasoning / generation — the costly path; fast cloud, then local, then
    # the fast 1b local model so a slow large model can't blow the timeout.
    "reason":     Tier(chain=["openai:gpt-4o-mini", "local:mistral", "local:llama3.2:1b"],
                       max_tokens=1536, temperature=0.2),
    # Long-form synthesis of collected material.
    "synthesize": Tier(chain=["openai:gpt-4o-mini", "local:mistral"],
                       max_tokens=1024, temperature=0.1),
    # Drafting / writing — a touch warmer.
    "draft":      Tier(chain=["openai:gpt-4o-mini", "local:mistral"],
                       max_tokens=1024, temperature=0.3),
    # Background scheduled/reflexion agents — LOCAL-FIRST to keep the many
    # scheduled runs off the paid cloud key (user's explicit cost decision).
    # No cloud in the chain; if both local models are unusable the caller's
    # legacy fallback path handles it.
    "background": Tier(chain=["local:mistral", "local:llama3.2:1b"],
                       max_tokens=1024, temperature=0.2),
}

_DEFAULT_TASK = "reason"


def _tier(task_type: str) -> Tier:
    return ROUTING.get(task_type) or ROUTING[_DEFAULT_TASK]


# ── Circuit breaker (shared across workers via hub_config) ──────────────────────
_LOCAL_OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/v1"

# Trip durations.
_TRIP_LONG_SECONDS = int(os.environ.get("GATEWAY_BREAKER_LONG", str(6 * 3600)))   # dead key
_TRIP_SHORT_SECONDS = int(os.environ.get("GATEWAY_BREAKER_SHORT", "120"))          # transient

# Auth-shaped error markers → long trip. Kept in sync with free_llm_keys.
_AUTH_MARKERS = (
    "401", "invalid api key", "incorrect api key", "invalid_api_key",
    "unauthorized", "authentication", "no such key", "permission",
)
# Transient (timeout / 5xx / connection) markers → short trip. Anything not
# clearly auth-shaped is treated as transient so a real dead key is the only
# thing that gets a long trip.
_TRANSIENT_MARKERS = (
    "timeout", "timed out", "500", "502", "503", "504", "429",
    "connection", "refused", "unavailable", "temporarily",
)


def _breaker_key(provider: str) -> str:
    return f"breaker_{provider}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _breaker_open(provider: str) -> bool:
    """True if provider's breaker is currently OPEN (shared hub_config state)."""
    try:
        import hub_db
        state = hub_db.get_config(_breaker_key(provider))
    except Exception as exc:  # DB unreachable → fail open (allow the call)
        _safe_log("debug", "breaker read failed for %s: %s", provider, exc)
        return False
    if not isinstance(state, dict):
        return False
    open_until = state.get("open_until")
    if not open_until:
        return False
    try:
        until = datetime.fromisoformat(open_until)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return _now() < until


def _trip(provider: str, seconds: int) -> None:
    """Open provider's breaker for `seconds`, persisted so all workers see it."""
    try:
        import hub_db
        open_until = (_now() + timedelta(seconds=seconds)).isoformat()
        hub_db.set_config(_breaker_key(provider), {"open_until": open_until})
        _safe_log("warning", "breaker tripped: %s open for %ss", provider, seconds)
    except Exception as exc:
        _safe_log("debug", "breaker trip failed for %s: %s", provider, exc)


def _is_auth_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _AUTH_MARKERS)


def _is_transient_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if any(m in msg for m in _TRANSIENT_MARKERS):
        return True
    # LangChain/openai timeout exception classes by name.
    name = type(exc).__name__.lower()
    return "timeout" in name or "connection" in name


def _safe_log(level: str, fmt: str, *args) -> None:
    try:
        getattr(logger, level, logger.info)(fmt, *args)
    except Exception:
        pass


# ── Provider resolution ─────────────────────────────────────────────────────────
def _resolve(provider_id: str) -> dict[str, str]:
    """Map a chain identifier to build_llm kwargs.

    "openai:<model>" → provider=openai, api_key from hub_config['llm_key_openai']
    "local:<model>"  → provider=ollama, base_url localhost:11434/v1
    "<prov>:<model>" → generic passthrough (base_url/key resolved by build_llm)
    """
    if ":" not in provider_id:
        # Bare provider name with no model — nothing we can build.
        return {"provider": provider_id, "model": "", "base_url": "", "api_key": ""}
    scheme, model = provider_id.split(":", 1)
    scheme = scheme.strip().lower()

    if scheme == "local":
        return {"provider": "ollama", "model": model,
                "base_url": _LOCAL_OLLAMA_BASE, "api_key": "ollama"}

    if scheme == "openai":
        return {"provider": "openai", "model": model, "base_url": "",
                "api_key": _openai_key()}

    # Fallback: treat scheme as the provider directly (github, groq, anthropic…).
    return {"provider": scheme, "model": model, "base_url": "", "api_key": ""}


def _openai_key() -> str:
    try:
        import hub_db
        key = hub_db.get_config("llm_key_openai") or ""
    except Exception:
        key = ""
    return key or os.environ.get("OPENAI_API_KEY", "")


def _build(spec: dict[str, str], temperature: float, max_tokens: int, json_mode: bool):
    """Construct a (possibly json-bound) LangChain model via llm_router.build_llm."""
    from llm_router import build_llm
    # Bound max_tokens for this call via the env knob build_llm reads.
    prev = os.environ.get("AGENT_LLM_MAX_TOKENS")
    try:
        os.environ["AGENT_LLM_MAX_TOKENS"] = str(max_tokens)
        model = build_llm(
            provider=spec["provider"],
            model=spec["model"],
            base_url=spec.get("base_url", ""),
            api_key=spec.get("api_key", ""),
            temperature=temperature,
        )
    finally:
        if prev is None:
            os.environ.pop("AGENT_LLM_MAX_TOKENS", None)
        else:
            os.environ["AGENT_LLM_MAX_TOKENS"] = prev

    if json_mode:
        model = _bind_json(model)
    return model


def _bind_json(model):
    """Bind response_format=json_object for OpenAI-compatible models (incl. Ollama).

    Mirrors agent_runner._json_llm — non-OpenAI models pass through unchanged.
    """
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
        if isinstance(model, ChatOpenAI):
            return model.bind(response_format={"type": "json_object"})
    except Exception:
        pass
    return model


def _message_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


# ── Public API ──────────────────────────────────────────────────────────────────
class AllProvidersDown(RuntimeError):
    """Raised when every provider in a task's fallback chain is unusable."""


def complete(task_type: str, messages: list, *, json: bool = False,
             temperature: float | None = None, max_tokens: int | None = None) -> str:
    """Run `messages` through the fallback chain for `task_type`, return the text.

    Walks ROUTING[task_type].chain; skips providers whose breaker is OPEN, builds
    each via llm_router.build_llm, and invokes it. On auth/401-shaped errors trips
    the breaker LONG (~6h); on timeout/5xx/transient errors trips SHORT (~2m); then
    continues to the next provider. Raises AllProvidersDown only if the whole chain
    is exhausted.
    """
    tier = _tier(task_type)
    use_json = json or tier.json
    temp = tier.temperature if temperature is None else temperature
    toks = tier.max_tokens if max_tokens is None else max_tokens

    last_exc: BaseException | None = None
    skipped: list[str] = []

    for provider_id in tier.chain:
        if _breaker_open(provider_id):
            skipped.append(provider_id)
            continue
        spec = _resolve(provider_id)
        if not spec.get("model"):
            continue
        started = _now()
        try:
            model = _build(spec, temp, toks, use_json)
            response = model.invoke(messages)
            text = _message_text(response)
            _safe_log(
                "debug", "gateway %s via %s ok (%.1fs)",
                task_type, provider_id, (_now() - started).total_seconds(),
            )
            return text
        except Exception as exc:
            last_exc = exc
            # Keep the free-key subsystem in sync on auth failures.
            try:
                import free_llm_keys as _fk
                _fk.note_free_call_failure(exc)
            except Exception:
                pass
            if _is_auth_error(exc):
                _trip(provider_id, _TRIP_LONG_SECONDS)
                _safe_log("warning", "gateway %s auth-failed on %s: %s",
                          task_type, provider_id, str(exc)[:200])
            else:
                # Timeouts, 5xx, connection errors, and anything else → short trip.
                _trip(provider_id, _TRIP_SHORT_SECONDS)
                _safe_log("warning", "gateway %s error on %s (%s): %s",
                          task_type, provider_id, type(exc).__name__, str(exc)[:200])
            continue

    raise AllProvidersDown(
        f"All providers exhausted for task_type={task_type!r} "
        f"(chain={tier.chain}, skipped_open={skipped}, last_error={last_exc})"
    )


def build_model(task_type: str = _DEFAULT_TASK, *, json: bool = False,
                temperature: float | None = None, max_tokens: int | None = None):
    """Return a ready-to-`.invoke()` LangChain model for `task_type`.

    Backward-compatibility helper for the three legacy factories, which all return
    a *model object* (callers do `model.invoke(messages)`) rather than text. This
    picks the first provider in ROUTING[task_type].chain whose breaker is CLOSED
    and whose spec is buildable, builds it via llm_router.build_llm (applying the
    tier's json/temperature/max_tokens defaults), and returns it. Raises
    AllProvidersDown if none are usable so callers can fall back to their old path.
    """
    tier = _tier(task_type)
    use_json = json or tier.json
    temp = tier.temperature if temperature is None else temperature
    toks = tier.max_tokens if max_tokens is None else max_tokens

    skipped: list[str] = []
    last_exc: BaseException | None = None
    for provider_id in tier.chain:
        if _breaker_open(provider_id):
            skipped.append(provider_id)
            continue
        spec = _resolve(provider_id)
        if not spec.get("model"):
            continue
        try:
            return _build(spec, temp, toks, use_json)
        except Exception as exc:
            last_exc = exc
            _trip(provider_id, _TRIP_SHORT_SECONDS)
            _safe_log("warning", "gateway build_model %s failed on %s: %s",
                      task_type, provider_id, str(exc)[:200])
            continue

    raise AllProvidersDown(
        f"build_model: no usable provider for task_type={task_type!r} "
        f"(chain={tier.chain}, skipped_open={skipped}, last_error={last_exc})"
    )


def task_for_weight(weight: str = "light") -> str:
    """Map the legacy `weight` argument to a gateway task_type.

    "heavy" was the costly main reasoning/generation call → "reason".
    "light" was cheaper auxiliary calls → also "reason" (the chain already
    fronts the fast cloud model, then local fallbacks), keeping behavior close to
    the old default while going through one routing policy.
    """
    return "reason"


__all__ = [
    "ROUTING", "Tier", "complete", "build_model", "task_for_weight",
    "AllProvidersDown", "_breaker_open", "_trip",
]
