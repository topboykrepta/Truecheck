from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException

from app.config import settings
from app.db import get_session
from app.models import AuditEvent, Claim, EvidenceItem, OriginTrace, Report
from app.schemas import AuditResponse, Citation, ClaimRow, ReportResponse


def build_report_response(report_id: str) -> ReportResponse:
    with get_session() as session:
        report = session.get(Report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="report not found")

        claims = session.query(Claim).filter(Claim.report_id == report_id).all()
        evidence = session.query(EvidenceItem).filter(EvidenceItem.report_id == report_id).all()
        origin = session.query(OriginTrace).filter(OriginTrace.report_id == report_id).first()
        limitations_events = session.query(AuditEvent).filter(
            AuditEvent.report_id == report_id, AuditEvent.event_type == "limitations"
        ).all()

    key_claims: list[ClaimRow] = []
    for c in claims:
        citations: list[Citation] = []

        # Prefer the exact citations Gemini referenced (from stored reasoning snapshot).
        reasoning = None
        if getattr(c, "reasoning_json", None):
            try:
                reasoning = json.loads(c.reasoning_json) if c.reasoning_json else None
            except Exception:
                reasoning = None

        if reasoning and isinstance(reasoning, dict) and isinstance(reasoning.get("evidence"), list):
            ev_list = reasoning.get("evidence") or []
            cited = reasoning.get("citations") or []
            for idx in cited[:5]:
                try:
                    i = int(idx) - 1
                except Exception:
                    continue
                if 0 <= i < len(ev_list):
                    ev = ev_list[i] or {}
                    citations.append(
                        Citation(
                            url=ev.get("url") or "",
                            publisher=ev.get("publisher"),
                            date=ev.get("published_date"),
                            snippet=ev.get("snippet"),
                            credibility=ev.get("credibility"),
                        )
                    )
        else:
            # Fallback: first few web extracts for the claim.
            web_evidence = [e for e in evidence if e.kind == "web_extract" and e.claim_id == c.id]
            for ev in web_evidence[:3]:
                citations.append(
                    Citation(
                        url=ev.url,
                        publisher=ev.publisher,
                        date=ev.published_date,
                        snippet=ev.snippet,
                        credibility=(ev.credibility.value if ev.credibility else None),
                    )
                )
        key_claims.append(
            ClaimRow(
                claim_text=c.claim_text,
                status=c.status,
                confidence=c.confidence,
                rationale=getattr(c, "rationale", None),
                citations=citations,
            )
        )

    evidence_gallery = {
        "web_extracts": [
            {
                "url": e.url,
                "publisher": e.publisher,
                "date": e.published_date,
                "title": e.title,
                "snippet": e.snippet,
                "thumbnail_url": e.thumbnail_url,
                "credibility": (e.credibility.value if e.credibility else None),
            }
            for e in evidence
            if e.kind == "web_extract"
        ],
        "image_matches": [
            {
                "url": e.url,
                "publisher": e.publisher,
                "date": e.published_date,
                "title": e.title,
                "thumbnail_url": e.thumbnail_url,
                "credibility": (e.credibility.value if e.credibility else None),
            }
            for e in evidence
            if e.kind == "image_match"
        ][: max(0, int(settings.truecheck_max_image_matches_total))],
        "trusted_sources": [
            {
                "url": e.url,
                "publisher": e.publisher,
                "date": e.published_date,
                "title": e.title,
                "snippet": e.snippet,
                "credibility": (e.credibility.value if e.credibility else None),
            }
            for e in evidence
            if (e.credibility and e.credibility.value == "Trusted")
        ],
    }

    origin_tracing = {
        "most_likely_origin_urls": [origin.likely_origin_url] if origin and origin.likely_origin_url else [],
        "earliest_appearance": origin.earliest_appearance if origin else None,
        "timeline": json.loads(origin.timeline_json) if origin and origin.timeline_json else [],
    }

    limitations: list[str] = []
    for ev in limitations_events:
        try:
            limitations.extend(json.loads(ev.details_json).get("items") or [])
        except Exception:
            pass

    return ReportResponse(
        report_id=report.id,
        created_at=report.created_at,
        updated_at=report.updated_at,
        input_type=report.input_type.value,
        status=report.status.value,
        verdict=(report.verdict.value if report.verdict else None),
        confidence=report.confidence,
        ai_likelihood=report.ai_likelihood,
        explanation=report.explanation,
        key_claims=key_claims,
        evidence=evidence_gallery,
        origin_tracing=origin_tracing,
        limitations=limitations,
    )


def build_audit_response(report_id: str) -> AuditResponse:
    with get_session() as session:
        events = session.query(AuditEvent).filter(AuditEvent.report_id == report_id).order_by(AuditEvent.created_at).all()

    return AuditResponse(
        report_id=report_id,
        events=[
            {
                "time": e.created_at.isoformat(),
                "type": e.event_type,
                "details": json.loads(e.details_json) if e.details_json else {},
            }
            for e in events
        ],
    )
