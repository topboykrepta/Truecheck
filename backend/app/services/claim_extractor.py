from __future__ import annotations

import re

from app.services.safety import sanitize_untrusted_text


def extract_claims(text: str, max_claims: int = 6) -> list[str]:
    """Rules-based claim splitter.

    This is deterministic and explainable. If Gemini is configured, you can later
    replace/augment with an LLM-based extractor.
    """
    text = sanitize_untrusted_text(text, max_len=12000)

    # Simple sentence-ish split; keeps it predictable.
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]

    # Heuristic: pick sentences that look like factual claims.
    candidates: list[str] = []
    for p in parts:
        if len(p) < 12:
            continue
        if re.search(r"\b(according to|report|reports|said|claims|confirmed|denied)\b", p, re.I):
            candidates.append(p)
        elif re.search(r"\b\d{4}\b|\b\d+%\b|\b\d+\b", p):
            candidates.append(p)
        elif re.search(r"\b(is|are|was|were|will|has|have|had)\b", p, re.I):
            candidates.append(p)

    # De-dupe while preserving order.
    seen = set()
    uniq: list[str] = []
    for c in candidates:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)

    return uniq[:max_claims] if uniq else parts[: min(max_claims, len(parts))]
