from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlmodel import select

from app.config import settings
from app.db import get_session
from app.models import SearchCache


def cache_get(kind: str, query: str):
    now = datetime.utcnow()
    with get_session() as session:
        stmt = (
            select(SearchCache)
            .where(SearchCache.kind == kind)
            .where(SearchCache.query == query)
            .where(SearchCache.expires_at > now)
            .order_by(SearchCache.created_at.desc())
            .limit(1)
        )
        hit = session.exec(stmt).first()
        if not hit:
            return None
        try:
            return json.loads(hit.response_json)
        except Exception:
            return None


def cache_put(kind: str, query: str, response_obj) -> None:
    ttl = max(0, int(settings.truecheck_search_cache_ttl_seconds))
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)

    payload = json.dumps(response_obj)
    with get_session() as session:
        session.add(SearchCache(kind=kind, query=query, response_json=payload, expires_at=expires_at))
        session.commit()
