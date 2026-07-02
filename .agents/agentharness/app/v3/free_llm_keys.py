"""free_llm_keys.py — Daily scraper for free LLM API keys.

Fetches the README from https://github.com/alistaitsacle/free-llm-api-keys,
parses all available keys, tests each key via the proxy API, and saves the
first working key per provider into the ArchonHub hub_db.

Base URL: https://aiapiv2.pekpik.com/v1
All keys are OpenAI-compatible.

Features:
  - Stale key detection: keys are disabled if synced_date != today
  - Pre-use validation with 30-min TTL cache (validate_provider_key)
  - Retry state helpers: get/set retry count for scheduler retry logic

Usage (standalone):
    python free_llm_keys.py

Usage (as module):
    from free_llm_keys import sync_free_keys, validate_provider_key, are_keys_stale
    result = sync_free_keys()
"""

from __future__ import annotations

import json
import re
import threading
import urllib.request
import urllib.error
from datetime import date, datetime, timezone, timedelta
from typing import Any

try:
    from ah_logging import get_logger
except Exception:
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(f"archonhub.{name}")

try:
    from hub_db import update_config as _hub_update_config, get_config as _hub_get_config, save_notification
except Exception:
    _hub_update_config = None
    _hub_get_config = None
    save_notification = None

logger = get_logger("free_llm_keys")

# ── Constants ──────────────────────────────────────────────────────────────────

README_URL = "https://raw.githubusercontent.com/alistaitsacle/free-llm-api-keys/main/README.md"
BASE_URL = "https://aiapiv2.pekpik.com/v1"
FETCH_TIMEOUT = 15   # seconds for README fetch
TEST_TIMEOUT = 6     # seconds per key test call
MAX_CANDIDATES = 3   # max keys to test per provider before giving up
VALIDATION_TTL = 1800  # seconds (30 min) to cache key validation results
MAX_RETRIES_PER_DAY = 2  # max scheduler retries on sync failure

# ── In-memory validation cache ─────────────────────────────────────────────────
# { provider: (is_valid: bool, expires_at: datetime) }
_validation_cache: dict[str, tuple[bool, datetime]] = {}
_cache_lock = threading.Lock()

# Regex: captures key and model from a markdown table row
# e.g.  | `sk-abc123...` | claude-opus-4-7 | 🆕 New | $20 | ...
KEY_ROW_RE = re.compile(
    r"\|\s*`(sk-[A-Za-z0-9]+)`\s*\|\s*([^\|]+?)\s*\|"
)

# Model name → provider label used in hub DB (llm_key_{provider})
MODEL_TO_PROVIDER: dict[str, str] = {
    "claude":      "anthropic",
    "gemini":      "google",
    "gpt":         "openai",
    "openai/":     "openai",
    "grok":        "xai",
    "x-ai/":       "xai",
    "deepseek":    "deepseek",
    "kimi":        "moonshot",
    "moonshot":    "moonshot",
    "qwen":        "alibaba",
    "smart-chat":  "smart",
    "mistral":     "mistral",
    "llama":       "meta",
    "perplexity":  "perplexity",
}

# Provider → preferred test model (for validation call)
PROVIDER_TEST_MODEL: dict[str, str] = {
    "anthropic":  "claude-opus-4-7",
    "google":     "gemini-2.5-flash",
    "openai":     "gpt-5.5",
    "xai":        "grok-4.3",
    "deepseek":   "deepseek-chat",
    "moonshot":   "kimi-k2.5",
    "smart":      "smart-chat",
    "alibaba":    "qwen3.5-plus-20260420",
    "mistral":    "mistral-large",
    "meta":       "llama-3-70b",
    "perplexity": "llama-3.1-sonar-large-128k-online",
}


# ── Key parsing ────────────────────────────────────────────────────────────────

def _provider_from_model(model: str) -> str:
    """Map a model name to a provider label."""
    model_lower = model.lower().strip()
    for prefix, provider in MODEL_TO_PROVIDER.items():
        if model_lower.startswith(prefix) or f"/{prefix}" in model_lower:
            return provider
    return "unknown"


def fetch_readme() -> str:
    """Download the README from GitHub. Returns raw text."""
    req = urllib.request.Request(README_URL, headers={"User-Agent": "ArchonHub/1.0"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_keys(readme: str) -> dict[str, list[dict]]:
    """
    Parse all key rows from the README markdown tables.

    Returns a dict: provider -> list of {key, model, provider}
    """
    providers: dict[str, list[dict]] = {}
    for match in KEY_ROW_RE.finditer(readme):
        key = match.group(1).strip()
        model = match.group(2).strip()
        if len(key) < 20 or not model:
            continue
        provider = _provider_from_model(model)
        if provider == "unknown":
            continue
        providers.setdefault(provider, []).append({"key": key, "model": model, "provider": provider})
    return providers


# ── Key validation ─────────────────────────────────────────────────────────────

def _test_key(key: str, model: str) -> bool:
    """
    Send a minimal chat completion request to verify the key is valid and has budget.
    Returns True if the response is a valid completion (even a tiny one).
    """
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "ArchonHub/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TEST_TIMEOUT) as resp:
            body = json.loads(resp.read())
            return bool(body.get("choices"))
    except urllib.error.HTTPError as e:
        # 402 = out of budget, 401 = bad key, 429 = rate limited
        logger.debug("Key test HTTP %s for model %s", e.code, model)
        return False
    except Exception as e:
        logger.debug("Key test error for model %s: %s", model, e)
        return False


def find_working_key(candidates: list[dict]) -> dict | None:
    """
    Try up to MAX_CANDIDATES keys in parallel (3 at a time) until one passes.
    Returns the first working entry or None.
    """
    import concurrent.futures

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c["key"] not in seen:
            seen.add(c["key"])
            unique.append(c)

    batch = unique[:MAX_CANDIDATES]
    result_holder: list[dict] = []

    def _try(entry: dict) -> dict | None:
        logger.debug("Testing key ...%s for %s", entry["key"][-6:], entry["model"])
        if _test_key(entry["key"], entry["model"]):
            logger.info("Found working key for %s (%s)", entry["provider"], entry["model"])
            return entry
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(batch))) as ex:
        futures = {ex.submit(_try, e): e for e in batch}
        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
                if res:
                    result_holder.append(res)
                    # Cancel remaining futures (best-effort)
                    for f in futures:
                        f.cancel()
                    break
            except Exception:
                pass

    return result_holder[0] if result_holder else None


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _save_provider_key(provider: str, key: str, model: str) -> None:
    """Persist a working key into hub_db settings."""
    if not callable(_hub_update_config):
        return
    try:
        _hub_update_config({
            f"llm_key_{provider}": key,
            f"llm_model_{provider}_free": model,
            f"llm_enabled_{provider}": "1",
            f"llm_base_url_{provider}": BASE_URL,
        })
    except Exception:
        logger.exception("Failed saving key for provider %s", provider)


def _record_sync_time() -> None:
    if not callable(_hub_update_config):
        return
    try:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        today = date.today().isoformat()
        _hub_update_config({
            "free_llm_keys_last_sync": now_iso,
            "free_llm_keys_synced_date": today,
        })
    except Exception:
        pass


def get_last_sync_time() -> str | None:
    if not callable(_hub_get_config):
        return None
    try:
        return _hub_get_config("free_llm_keys_last_sync")
    except Exception:
        return None


# ── Stale key detection ────────────────────────────────────────────────────────

def are_keys_stale() -> bool:
    """Return True if the last successful sync was not today."""
    if not callable(_hub_get_config):
        return False
    try:
        synced_date = _hub_get_config("free_llm_keys_synced_date") or ""
        return synced_date != date.today().isoformat()
    except Exception:
        return True


def disable_stale_keys() -> list[str]:
    """
    Set llm_enabled_{provider}="0" for all free-key providers whose keys are stale.
    Returns list of providers disabled.
    Clears the in-memory validation cache.
    """
    if not callable(_hub_update_config) or not callable(_hub_get_config):
        return []
    disabled = []
    try:
        for provider in set(MODEL_TO_PROVIDER.values()):
            base_url = _hub_get_config(f"llm_base_url_{provider}") or ""
            if base_url == BASE_URL:
                _hub_update_config({f"llm_enabled_{provider}": "0"})
                disabled.append(provider)
        with _cache_lock:
            _validation_cache.clear()
        if disabled:
            logger.info("Disabled %d stale free-key providers: %s", len(disabled), disabled)
    except Exception:
        logger.exception("Error disabling stale keys")
    return disabled


# ── Pre-use key validation ─────────────────────────────────────────────────────

def validate_provider_key(provider: str) -> bool:
    """
    Validate the stored free key for *provider* is still working.
    Results are cached for VALIDATION_TTL seconds (30 min).
    Returns False if no key stored, key invalid, or provider disabled.
    """
    now = datetime.now(timezone.utc)
    with _cache_lock:
        cached = _validation_cache.get(provider)
        if cached:
            is_valid, expires_at = cached
            if now < expires_at:
                return is_valid
            del _validation_cache[provider]

    if not callable(_hub_get_config) or not callable(_hub_update_config):
        return False

    try:
        enabled = _hub_get_config(f"llm_enabled_{provider}") or "0"
        if enabled != "1":
            return False

        key = _hub_get_config(f"llm_key_{provider}") or ""
        if not key:
            return False

        base_url = _hub_get_config(f"llm_base_url_{provider}") or ""
        if base_url != BASE_URL:
            return False  # not a free-proxy key — don't validate here

        model = _hub_get_config(f"llm_model_{provider}_free") or PROVIDER_TEST_MODEL.get(provider, "")
        if not model:
            return False

        is_valid = _test_key(key, model)
        if not is_valid:
            logger.warning("Stored free key for %s is no longer valid — disabling", provider)
            _hub_update_config({f"llm_enabled_{provider}": "0"})
        else:
            logger.debug("Free key for %s validated OK", provider)

        expires_at = now + timedelta(seconds=VALIDATION_TTL)
        with _cache_lock:
            _validation_cache[provider] = (is_valid, expires_at)
        return is_valid
    except Exception:
        logger.exception("Error validating key for provider %s", provider)
        return False


# ── Round-robin load balancing across enabled free providers ────────────────────
# Spreads LLM calls across the enabled+validated free keys so no single key gets
# hammered (each free key has its own rate limit). State is module-level so all
# callers (hub_nodes._llm, llm_router) share one rotation.
_rr_lock = threading.Lock()
_rr_index = 0
# Provider returned by the most recent next_free_provider() pick, so a caller
# that hits a live auth failure can disable exactly that provider.
_last_pick: str | None = None


def get_usable_free_providers() -> list[str]:
    """Return enabled free providers that have a key + model and pass validation.

    Insertion-order of MODEL_TO_PROVIDER is preserved (dedup). Validation uses the
    30-min cache, so this is cheap to call on the hot path.
    """
    out: list[str] = []
    if not callable(_hub_get_config):
        return out
    for p in dict.fromkeys(MODEL_TO_PROVIDER.values()):
        try:
            if (_hub_get_config(f"llm_enabled_{p}") or "0") != "1":
                continue
            if not (_hub_get_config(f"llm_key_{p}") or ""):
                continue
            if not (_hub_get_config(f"llm_model_{p}_free") or ""):
                continue
            if validate_provider_key(p):
                out.append(p)
        except Exception:
            continue
    return out


def next_free_provider() -> tuple[str, str, str] | None:
    """Round-robin pick of a usable free provider.

    Returns (provider, api_key, model) for the next provider in rotation, or None
    when no free provider is currently usable. Use BASE_URL as the base_url.
    """
    providers = get_usable_free_providers()
    if not providers:
        return None
    global _rr_index, _last_pick
    with _rr_lock:
        provider = providers[_rr_index % len(providers)]
        _rr_index += 1
    key = _hub_get_config(f"llm_key_{provider}") or ""
    model = _hub_get_config(f"llm_model_{provider}_free") or ""
    if not key or not model:
        return None
    _last_pick = provider
    return (provider, key, model)


_AUTH_ERROR_MARKERS = (
    "401", "invalid api key", "incorrect api key", "invalid_api_key",
    "unauthorized", "authentication", "no such key",
)


def note_free_call_failure(exc: object, provider: str | None = None) -> str | None:
    """Disable a free provider after a *live* auth failure (e.g. 401).

    Periodic validation (validate_provider_key) can pass a key that then 401s on
    real calls (expired/quota). When a caller catches such an error it passes the
    exception here; if it looks auth-related we disable that provider (defaults to
    the last one picked) and cache it invalid for 6h so it is not reselected until
    the next successful key sync. Non-auth errors (timeouts, etc.) are ignored.
    """
    msg = str(exc).lower()
    if not any(m in msg for m in _AUTH_ERROR_MARKERS):
        return None
    p = provider or _last_pick
    if not p or not callable(_hub_update_config):
        return None
    try:
        _hub_update_config({f"llm_enabled_{p}": "0"})
        with _cache_lock:
            _validation_cache[p] = (False, datetime.now(timezone.utc) + timedelta(hours=6))
        logger.warning("Disabled free provider %s after live auth failure: %s", p, str(exc)[:160])
    except Exception:
        logger.exception("Failed disabling free provider %s", p)
    return p


# ── Retry state helpers ────────────────────────────────────────────────────────

def get_retry_count() -> int:
    """Return today's retry count (resets to 0 on a new day)."""
    if not callable(_hub_get_config):
        return 0
    try:
        retry_date = _hub_get_config("free_llm_keys_retry_date") or ""
        if retry_date != date.today().isoformat():
            return 0
        return int(_hub_get_config("free_llm_keys_retry_count") or "0")
    except Exception:
        return 0


def increment_retry_count() -> int:
    """Increment today's retry count. Returns the new count."""
    if not callable(_hub_update_config):
        return 0
    try:
        today = date.today().isoformat()
        count = get_retry_count() + 1
        _hub_update_config({
            "free_llm_keys_retry_date": today,
            "free_llm_keys_retry_count": str(count),
        })
        return count
    except Exception:
        return 0


# ── Main sync ──────────────────────────────────────────────────────────────────

def sync_free_keys(providers_to_sync: list[str] | None = None) -> dict[str, Any]:
    """
    Full sync: fetch README, parse keys, test, save working keys.

    Args:
        providers_to_sync: optional list of provider names to limit sync.
                           None means sync all discovered providers.

    Returns:
        {
            "synced": {provider: model, ...},   # providers where a working key was found
            "failed": [provider, ...],          # providers with no working key
            "total_keys_found": int,
            "timestamp": str,
        }
    """
    logger.info("Starting free LLM key sync from %s", README_URL)
    synced: dict[str, str] = {}
    failed: list[str] = []
    total_keys = 0

    # Disable stale keys up-front so agents don't use yesterday's dead keys
    # during the sync window.
    if are_keys_stale():
        disable_stale_keys()

    try:
        readme = fetch_readme()
        logger.info("README fetched (%d chars)", len(readme))
    except Exception as e:
        logger.error("Failed to fetch README: %s", e)
        return {"synced": {}, "failed": [], "error": str(e), "total_keys_found": 0}

    all_providers = parse_keys(readme)
    total_keys = sum(len(v) for v in all_providers.values())
    logger.info("Parsed %d keys across %d providers", total_keys, len(all_providers))

    target_providers = providers_to_sync or list(all_providers.keys())

    for provider in target_providers:
        candidates = all_providers.get(provider, [])
        if not candidates:
            logger.debug("No keys found for provider %s", provider)
            failed.append(provider)
            continue

        working = find_working_key(candidates)
        if working:
            _save_provider_key(provider, working["key"], working["model"])
            synced[provider] = working["model"]
        else:
            logger.warning("No working key found for provider %s (%d candidates tested)", provider, len(candidates))
            failed.append(provider)

    _record_sync_time()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    # Clear validation cache so the new keys are tested fresh on next use
    with _cache_lock:
        _validation_cache.clear()

    summary = (
        f"Free LLM key sync complete: {len(synced)} providers activated "
        f"({', '.join(synced.keys()) or 'none'})"
    )
    logger.info(summary)
    if callable(save_notification):
        try:
            save_notification(summary)
        except Exception:
            pass

    return {
        "synced": synced,
        "failed": failed,
        "total_keys_found": total_keys,
        "timestamp": ts,
    }


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    providers_arg = sys.argv[1:] or None  # e.g. python free_llm_keys.py anthropic google

    result = sync_free_keys(providers_arg)
    print("\n=== Free LLM Key Sync Results ===")
    print(f"Timestamp : {result.get('timestamp')}")
    print(f"Keys found: {result.get('total_keys_found')}")
    print(f"Synced    : {result.get('synced')}")
    print(f"Failed    : {result.get('failed')}")
    if "error" in result:
        print(f"Error     : {result['error']}")
        sys.exit(1)
