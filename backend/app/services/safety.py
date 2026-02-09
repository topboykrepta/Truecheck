from __future__ import annotations

import re


INJECTION_PATTERNS = [
    r"(?i)ignore\s+all\s+previous\s+instructions",
    r"(?i)system\s+prompt",
    r"(?i)you\s+are\s+chatgpt",
]


def strip_control_chars(text: str) -> str:
    return "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")


def redact_pii_like(text: str) -> str:
    # Lightweight redaction for common patterns. This is not exhaustive.
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED]", text)  # US SSN-like
    text = re.sub(r"\b\+?\d[\d\s\-]{7,}\b", "[REDACTED]", text)  # phone-like
    text = re.sub(r"\b[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[REDACTED]", text)
    return text


def sanitize_untrusted_text(text: str, max_len: int = 8000) -> str:
    text = strip_control_chars(text)
    text = redact_pii_like(text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len] + "\n[TRUNCATED]"
    return text


def looks_like_prompt_injection(text: str) -> bool:
    return any(re.search(pat, text or "") for pat in INJECTION_PATTERNS)
