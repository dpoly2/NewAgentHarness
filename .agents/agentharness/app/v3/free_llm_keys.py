"""free_llm_keys.py — Daily scraper for free LLM API keys.

Fetches the README from https://github.com/alistaitsacle/free-llm-api-keys,
parses all available keys, tests each key via the proxy API, and saves the
first working key per provider into the ArchonHub hub_db.

Base URL: https://aiapiv2.pekpik.com/v1
All keys are OpenAI-compatible.

Usage (standalone):
    python free_llm_keys.py

Usage (as module):
    from free_llm_keys import sync_free_keys
    result = sync_free_keys()
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
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
FETCH_TIMEOUT = 15  # seconds for README fetch
TEST_TIMEOUT = 6    # seconds per key test call
MAX_CANDIDATES = 3  # max keys to test per provider before giving up

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
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        _hub_update_config({"free_llm_keys_last_sync": now})
    except Exception:
        pass


def get_last_sync_time() -> str | None:
    if not callable(_hub_get_config):
        return None
    try:
        return _hub_get_config("free_llm_keys_last_sync")
    except Exception:
        return None


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
