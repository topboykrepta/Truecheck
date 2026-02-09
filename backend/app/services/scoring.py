from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dateutil import parser as dtparser


CREDIBILITY_WEIGHT = {
    "Trusted": 1.0,
    "Neutral": 0.8,
    "Unknown": 0.5,
    "Low credibility": 0.2,
}


@dataclass
class EvidenceSignal:
    credibility: str
    published_date: Optional[str] = None


def freshness_weight(published_date: Optional[str], now: Optional[datetime] = None) -> float:
    if not published_date:
        return 0.8
    now = now or datetime.utcnow()
    try:
        dt = dtparser.parse(published_date)
        days = max(0, (now - dt).days)
        # 0-30 days: 1.0 -> 0.9, 31-365: down to 0.7, older: 0.6
        if days <= 30:
            return 1.0 - (days / 300)
        if days <= 365:
            return 0.9 - ((days - 30) / 1675)
        return 0.6
    except Exception:
        return 0.75


def compute_claim_confidence(
    signals: list[EvidenceSignal],
    corroboration_count: int,
    has_conflict: bool,
) -> int:
    if not signals:
        return 25

    base = 0.0
    for s in signals:
        c = CREDIBILITY_WEIGHT.get(s.credibility, 0.5)
        f = freshness_weight(s.published_date)
        base += c * f
    base /= len(signals)

    # Corroboration boost: multiple independent sources increases confidence.
    corroboration_boost = min(0.15, 0.05 * max(0, corroboration_count - 1))

    # Conflict penalty: contradictory evidence reduces confidence.
    conflict_penalty = 0.25 if has_conflict else 0.0

    score = (base + corroboration_boost - conflict_penalty) * 100
    score = max(0, min(100, score))
    return int(round(score))
