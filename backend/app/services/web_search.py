from __future__ import annotations

from typing import Any, Optional

import httpx

from app.config import settings
from app.services.audit import audit
from app.services.cache import cache_get, cache_put
from app.services.safety import sanitize_untrusted_text


GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def _extract_thumbnail(pagemap: dict) -> str | None:
    try:
        thumbs = (pagemap or {}).get("cse_thumbnail") or []
        if thumbs and isinstance(thumbs, list):
            src = thumbs[0].get("src")
            if src:
                return src
        imgs = (pagemap or {}).get("cse_image") or []
        if imgs and isinstance(imgs, list):
            src = imgs[0].get("src")
            if src:
                return src
        metatags = (pagemap or {}).get("metatags") or []
        if metatags and isinstance(metatags, list):
            src = metatags[0].get("og:image")
            if src:
                return src
        return None
    except Exception:
        return None


def is_configured() -> bool:
    return bool(settings.google_cse_api_key and settings.google_cse_engine_id)


def search_web(report_id: str, query: str, num: int = 5) -> list[dict[str, Any]]:
    if not is_configured():
        audit(report_id, "web_search_skipped", {"reason": "GOOGLE_CSE not configured", "query": query})
        return []

    cache_key = f"q={query}|n={min(max(num, 1), 10)}"
    cached = cache_get("web", cache_key)
    if cached is not None:
        audit(report_id, "web_cache_hit", {"query": query})
        return cached

    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_engine_id,
        "q": query,
        "num": min(max(num, 1), 10),
    }

    audit(report_id, "web_search", {"query": query, "num": params["num"]})

    with httpx.Client(timeout=20) as client:
        resp = client.get(GOOGLE_CSE_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items") or []
    results: list[dict[str, Any]] = []
    for it in items:
        pagemap = it.get("pagemap") or {}
        results.append(
            {
                "url": it.get("link"),
                "title": sanitize_untrusted_text(it.get("title") or "", 500),
                "snippet": sanitize_untrusted_text(it.get("snippet") or "", 800),
                "displayLink": it.get("displayLink"),
                "thumbnail_url": _extract_thumbnail(pagemap),
                "pagemap": pagemap,
            }
        )

    cache_put("web", cache_key, results)
    return results


def search_images(report_id: str, query: str, num: int = 5) -> list[dict[str, Any]]:
    if not is_configured():
        audit(report_id, "image_search_skipped", {"reason": "GOOGLE_CSE not configured", "query": query})
        return []

    cache_key = f"q={query}|n={min(max(num, 1), 10)}"
    cached = cache_get("image", cache_key)
    if cached is not None:
        audit(report_id, "image_cache_hit", {"query": query})
        return cached

    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_engine_id,
        "q": query,
        "searchType": "image",
        "num": min(max(num, 1), 10),
    }

    audit(report_id, "image_search", {"query": query, "num": params["num"]})

    with httpx.Client(timeout=20) as client:
        resp = client.get(GOOGLE_CSE_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items") or []
    results: list[dict[str, Any]] = []
    for it in items:
        image = (it.get("image") or {})
        results.append(
            {
                "url": it.get("link"),
                "title": sanitize_untrusted_text(it.get("title") or "", 500),
                "thumbnail_url": image.get("thumbnailLink"),
                "displayLink": it.get("displayLink"),
            }
        )

    cache_put("image", cache_key, results)
    return results
