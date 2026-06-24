from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_admin_user, get_current_user
from core.config import HERE

router = APIRouter()

@router.post("/import")
async def run_data_import(admin_user: dict = Depends(get_admin_user)):
    """Trigger a full re-import of all markdown/JSON source files into the DB."""
    del admin_user
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "data_import", str(HERE / "data_import.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.import_all()
        return {"status": "ok", "imported": result}
    except Exception as exc:
        raise HTTPException(500, f"Import failed: {exc}") from exc

@router.post("/providers/sync-free-keys")
async def sync_free_llm_keys_endpoint(
    body: dict = None,
    current_user: dict = Depends(get_current_user),
):
    """Fetch and activate free daily LLM API keys from the public key registry."""
    del current_user
    try:
        import asyncio
        from free_llm_keys import sync_free_keys
        providers = (body or {}).get("providers")  # optional list to limit scope
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: sync_free_keys(providers))
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/free-keys-status")
async def free_keys_status(current_user: dict = Depends(get_current_user)):
    """Return last sync time and currently activated free-key providers."""
    del current_user
    try:
        from free_llm_keys import get_last_sync_time, MODEL_TO_PROVIDER
        import hub_db as _hdb
        last_sync = get_last_sync_time()
        providers_info = {}
        seen = set()
        for provider in set(MODEL_TO_PROVIDER.values()):
            if provider in seen:
                continue
            seen.add(provider)
            key = _hdb.get_config(f"llm_key_{provider}") or ""
            base_url = _hdb.get_config(f"llm_base_url_{provider}") or ""
            if base_url == "https://aiapiv2.pekpik.com/v1" and key:
                model = _hdb.get_config(f"llm_model_{provider}_free") or ""
                providers_info[provider] = {"model": model, "key_tail": key[-6:] if key else ""}
        return {
            "success": True,
            "last_sync": last_sync,
            "active_free_providers": providers_info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
