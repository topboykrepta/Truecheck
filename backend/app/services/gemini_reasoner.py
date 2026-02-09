from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import settings
from app.services.audit import audit
from app.services.safety import sanitize_untrusted_text


def is_configured() -> bool:
    return bool(settings.gemini_api_key)


def build_reasoning_prompt(claim: str, evidence: list[dict[str, Any]]) -> str:
    # IMPORTANT: reasoning must only use provided evidence; no invented sources.
    evidence_lines = []
    for idx, ev in enumerate(evidence, start=1):
        evidence_lines.append(
            f"[{idx}] URL: {ev.get('url')}\n"
            f"Publisher: {ev.get('publisher')}\n"
            f"Date: {ev.get('published_date')}\n"
            f"Snippet: {sanitize_untrusted_text(ev.get('snippet') or '', 800)}\n"
        )

    return (
        "You are a fact-checking assistant.\n"
        "Non-negotiable rules:\n"
        "- Use ONLY the evidence snippets provided below.\n"
        "- Do NOT invent new sources, URLs, quotes, or facts.\n"
        "- If evidence is insufficient or conflicting, set status=Unclear and explain what is missing.\n"
        "- Cite evidence ONLY by its bracketed number (e.g., [1], [3]).\n\n"
        "Output STRICT JSON (no markdown, no code fences) with keys:\n"
        "- status: one of Supported | Contradicted | Unclear\n"
        "- rationale: 3–8 sentences explaining why, explicitly referencing evidence numbers\n"
        "- citations: array of integers referencing the evidence items you relied on most\n\n"
        f"Claim: {sanitize_untrusted_text(claim, 600)}\n\n"
        "Evidence:\n" + "\n".join(evidence_lines)
    )


def _extract_json_object(text: str) -> str:
    t = (text or "").strip()
    # Strip common code fences.
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    t = t.strip()

    if t.startswith("{") and t.endswith("}"):
        return t

    # Best-effort: grab the first {...} block.
    m = re.search(r"\{[\s\S]*\}", t)
    if m:
        return m.group(0)
    return t


def gemini_rate_claim(report_id: str, claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    if not is_configured():
        audit(report_id, "gemini_skipped", {"reason": "GEMINI not configured"})
        return {"status": "Unclear", "rationale": "", "citations": []}

    prompt = build_reasoning_prompt(claim, evidence)
    audit(report_id, "gemini_call", {"model": settings.gemini_model, "evidence_count": len(evidence)})

    # Minimal Gemini REST call (Google AI Studio style). Exact APIs may evolve.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": settings.gemini_api_key}

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 900,
            "responseMimeType": "application/json",
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, params=params, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        text = _extract_json_object(text)
        # Best-effort JSON parse.
        result = json.loads(text) if text.startswith("{") else {"status": "Unclear", "rationale": text, "citations": []}
        return result
    except Exception as e:
        audit(report_id, "gemini_failed", {"error": str(e)})
        return {"status": "Unclear", "rationale": "", "citations": []}
