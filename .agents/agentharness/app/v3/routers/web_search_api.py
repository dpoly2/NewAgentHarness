from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import get_current_user

try:
    from ah_logging import get_logger
except ImportError:
    import logging
    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("web_search_api")
router = APIRouter()


@router.get("/search/web")
async def web_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    _: dict = Depends(get_current_user),
):
    """Perform a real-time web search via SerpAPI."""
    try:
        from web_search import SerpAPIClient
        client = SerpAPIClient()
        result = client.search(query=q, num_results=limit)
        return {
            "success": True,
            "query": result.query,
            "num_results": result.num_results,
            "search_timestamp": result.search_timestamp,
            "results": [s.to_dict() for s in result.sources],
        }
    except ValueError as e:
        # Key not configured or rate limit
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/web")
async def web_search_post(body: dict, _: dict = Depends(get_current_user)):
    """POST variant for web search (accepts {query, limit})."""
    q = body.get("query", "").strip()
    limit = min(int(body.get("limit", 5)), 20)
    if not q:
        raise HTTPException(status_code=400, detail="query is required")
    try:
        from web_search import SerpAPIClient
        client = SerpAPIClient()
        result = client.search(query=q, num_results=limit)
        return {
            "success": True,
            "query": result.query,
            "num_results": result.num_results,
            "search_timestamp": result.search_timestamp,
            "results": [s.to_dict() for s in result.sources],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/web/status")
async def web_search_status(_: dict = Depends(get_current_user)):
    """Check if web search is configured."""
    import os
    key = os.getenv("SERPAPI_API_KEY", "")
    return {
        "configured": bool(key),
        "provider": "SerpAPI (Google Search)",
        "key_hint": f"...{key[-4:]}" if len(key) > 4 else "(not set)",
    }
