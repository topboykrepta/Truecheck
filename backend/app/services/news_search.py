from __future__ import annotations

from typing import Any

import httpx

from app.services.audit import audit
from app.services.cache import cache_get, cache_put
from app.services.safety import sanitize_untrusted_text


GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


def search_gdelt(report_id: str, query: str, num: int = 5) -> list[dict[str, Any]]:
    """Optional second evidence API (no key required): GDELT 2.1 DOC.

    This is additive evidence and should be treated as neutral unless domain is trusted.
    """

    cache_key = f"q={query}|n={min(max(num, 1), 50)}"
    cached = cache_get("gdelt", cache_key)
    if cached is not None:
        audit(report_id, "gdelt_cache_hit", {"query": query})
        return cached

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": min(max(num, 1), 50),
        "sort": "HybridRel",
    }

    audit(report_id, "gdelt_search", {"query": query, "num": params["maxrecords"]})

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(GDELT_DOC_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()

        arts = data.get("articles") or []
        results: list[dict[str, Any]] = []
        for a in arts:
            results.append(
                {
                    "url": a.get("url"),
                    "title": sanitize_untrusted_text(a.get("title") or "", 500),
                    "snippet": sanitize_untrusted_text(a.get("seendate") or "", 120),
                    "publisher": sanitize_untrusted_text(a.get("sourceCountry") or "", 120) or None,
                    "published_date": a.get("seendate"),
                }
            )

        cache_put("gdelt", cache_key, results)
        return results
    except Exception as e:
        audit(report_id, "gdelt_failed", {"error": str(e)})
        return []
