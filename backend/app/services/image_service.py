"""Image search service — Pexels (primary) + Unsplash (fallback)."""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
_UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"

# Landscape orientation, reasonable size for 1920x1080 slides
_IMAGE_PARAMS = {
    "orientation": "landscape",
    "per_page": 12,
    "size": "large",
}


async def search_images(query: str, page: int = 1) -> dict:
    """Search images. Returns {"images": [...], "total": N, "provider": "..."}.

    Each image: {"id", "url", "preview", "alt", "width", "height", "photographer", "source"}.
    """
    query = query.strip()
    if not query:
        return {"images": [], "total": 0, "provider": ""}

    # Try Pexels first
    if settings.pexels_api_key:
        try:
            result = await _search_pexels(query, page)
            if result["images"]:
                return result
        except Exception:
            logger.warning("Pexels search failed", exc_info=True)

    # Fallback to Unsplash
    if settings.unsplash_access_key:
        try:
            result = await _search_unsplash(query, page)
            if result["images"]:
                return result
        except Exception:
            logger.warning("Unsplash search failed", exc_info=True)

    # No providers configured
    return {
        "images": [],
        "total": 0,
        "provider": "",
        "error": "未配置图片搜索 API 密钥。请在 .env 中设置 PEXELS_API_KEY（推荐）或 UNSPLASH_ACCESS_KEY。",
    }


async def _search_pexels(query: str, page: int) -> dict:
    params = {**_IMAGE_PARAMS, "query": query, "page": page}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            _PEXELS_SEARCH_URL,
            params=params,
            headers={"Authorization": settings.pexels_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    images = []
    for p in data.get("photos", []):
        images.append({
            "id": f"pexels-{p['id']}",
            "url": p["src"]["large2x"],        # ~1200px for proxy
            "preview": p["src"]["medium"],      # ~350px for thumbnails
            "alt": p.get("alt") or query,
            "width": p["width"],
            "height": p["height"],
            "photographer": p.get("photographer", ""),
            "source": "Pexels",
        })

    return {
        "images": images,
        "total": data.get("total_results", 0),
        "page": page,
        "provider": "Pexels",
    }


async def _search_unsplash(query: str, page: int) -> dict:
    params = {
        "query": query,
        "per_page": _IMAGE_PARAMS["per_page"],
        "page": page,
        "orientation": "landscape",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            _UNSPLASH_SEARCH_URL,
            params=params,
            headers={
                "Authorization": f"Client-ID {settings.unsplash_access_key}",
                "Accept-Version": "v1",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    images = []
    for r in data.get("results", []):
        images.append({
            "id": f"unsplash-{r['id']}",
            "url": r["urls"]["regular"],        # ~1080px
            "preview": r["urls"]["small"],      # ~400px
            "alt": r.get("alt_description") or r.get("description") or query,
            "width": r["width"],
            "height": r["height"],
            "photographer": r.get("user", {}).get("name", ""),
            "source": "Unsplash",
        })

    return {
        "images": images,
        "total": data.get("total", 0),
        "page": page,
        "provider": "Unsplash",
    }


async def proxy_image(url: str) -> tuple[bytes, str, str]:
    """Download an external image and return (content_bytes, content_type, filename).

    Used by the proxy endpoint so slides can embed images without CORS issues.
    Only allows Pexels and Unsplash domains.
    """
    allowed_prefixes = (
        "https://images.pexels.com/",
        "https://images.unsplash.com/",
    )
    if not any(url.startswith(p) for p in allowed_prefixes):
        raise ValueError("Only Pexels/Unsplash image URLs are allowed")

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "image/jpeg")
    filename = url.split("/")[-1].split("?")[0] or "image.jpg"

    return resp.content, content_type, filename
