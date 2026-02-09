from __future__ import annotations

import json
from datetime import datetime
from dateutil import parser as dtparser

from app.db import get_session
from app.config import settings
from app.models import (
    Claim,
    EvidenceItem,
    InputType,
    OriginTrace,
    Report,
    ReportStatus,
    Verdict,
)
from app.services.audit import audit
from app.services.audio_transcribe import transcribe_audio
from app.services.claim_extractor import extract_claims
from app.services.credibility import label_credibility
from app.services.gemini_reasoner import gemini_rate_claim
from app.services.image_ocr import ocr_image
from app.services.news_search import search_gdelt
from app.services.scoring import EvidenceSignal, compute_claim_confidence
from app.services.web_search import is_configured as google_is_configured
from app.services.web_search import search_images, search_web


def run_pipeline(report_id: str) -> None:
    """Main analysis pipeline. Runs in worker or background task."""
    with get_session() as session:
        report = session.get(Report, report_id)
        if not report:
            return
        report.status = ReportStatus.running
        report.updated_at = datetime.utcnow()
        session.add(report)
        session.commit()

    try:
        _run(report_id)
        with get_session() as session:
            report = session.get(Report, report_id)
            if report:
                report.status = ReportStatus.complete
                report.updated_at = datetime.utcnow()
                session.add(report)
                session.commit()
        audit(report_id, "complete", {})
    except Exception as e:
        with get_session() as session:
            report = session.get(Report, report_id)
            if report:
                report.status = ReportStatus.failed
                report.error_message = str(e)
                report.updated_at = datetime.utcnow()
                session.add(report)
                session.commit()
        audit(report_id, "failed", {"error": str(e)})


def _run(report_id: str) -> None:
    with get_session() as session:
        report = session.get(Report, report_id)
        if not report:
            return

    limitations: list[str] = []

    if report.input_type == InputType.text:
        text = report.input_text or ""
    elif report.input_type == InputType.image:
        text = ocr_image(report_id, report.storage_path or "")
        if not text:
            limitations.append("OCR unavailable or no text detected in image.")
    elif report.input_type == InputType.audio:
        text = transcribe_audio(report_id, report.storage_path or "")
        if not text:
            limitations.append("Transcription unavailable; install faster-whisper or provide transcript.")
    else:
        text = ""

    claims = extract_claims(text)
    audit(report_id, "claims_extracted", {"count": len(claims)})

    claim_rows: list[Claim] = []
    evidence_items: list[EvidenceItem] = []
    timeline_items: list[dict] = []

    total_web_evidence = 0

    for claim_text in claims:
        query = claim_text
        web_results = search_web(report_id, query, num=6)
        gdelt_results = search_gdelt(report_id, query, num=6)
        image_results = search_images(
            report_id,
            query,
            num=max(0, int(settings.truecheck_max_image_matches_per_claim)),
        )

        # Persist claim first so evidence can reference claim_id.
        with get_session() as session:
            claim_row = Claim(
                report_id=report_id,
                claim_text=claim_text,
                status="Unclear",
                confidence=0,
            )
            session.add(claim_row)
            session.commit()
            session.refresh(claim_row)

        claim_id = claim_row.id

        evidence_for_reasoner: list[dict] = []
        signals: list[EvidenceSignal] = []

        def _add_timeline(url: str | None, publisher: str | None, published_date: str | None, context: str | None):
            if not url or not published_date:
                return
            try:
                dt = dtparser.parse(published_date)
                timeline_items.append(
                    {
                        "date": dt.date().isoformat(),
                        "source": publisher,
                        "url": url,
                        "context": (context or "")[:240],
                    }
                )
            except Exception:
                return

        for wr in web_results:
            url = wr.get("url")
            pub = wr.get("displayLink")
            cred = label_credibility(url, pub)
            snippet = wr.get("snippet")
            thumbnail_url = wr.get("thumbnail_url")

            published_date = None
            # Best effort: some results include metatags.
            metatags = ((wr.get("pagemap") or {}).get("metatags") or [])
            if metatags and isinstance(metatags, list):
                published_date = metatags[0].get("article:published_time") or metatags[0].get("og:updated_time")

            evidence_for_reasoner.append(
                {
                    "url": url,
                    "publisher": pub,
                    "published_date": published_date,
                    "snippet": snippet,
                    "credibility": cred.value,
                }
            )
            signals.append(EvidenceSignal(credibility=cred.value, published_date=published_date))

            _add_timeline(url, pub, published_date, snippet)

            evidence_items.append(
                EvidenceItem(
                    report_id=report_id,
                    claim_id=claim_id,
                    kind="web_extract",
                    url=url or "",
                    publisher=pub,
                    published_date=published_date,
                    title=wr.get("title"),
                    snippet=snippet,
                    thumbnail_url=thumbnail_url,
                    credibility=cred,
                )
            )
            total_web_evidence += 1

        for gr in gdelt_results:
            url = gr.get("url")
            pub = gr.get("publisher")
            published_date = gr.get("published_date")
            snippet = gr.get("snippet")
            cred = label_credibility(url, pub)

            evidence_for_reasoner.append(
                {
                    "url": url,
                    "publisher": pub,
                    "published_date": published_date,
                    "snippet": snippet,
                    "credibility": cred.value,
                }
            )
            signals.append(EvidenceSignal(credibility=cred.value, published_date=published_date))
            _add_timeline(url, pub, published_date, snippet)

            evidence_items.append(
                EvidenceItem(
                    report_id=report_id,
                    claim_id=claim_id,
                    kind="web_extract",
                    url=url or "",
                    publisher=pub,
                    published_date=published_date,
                    title=gr.get("title"),
                    snippet=snippet,
                    credibility=cred,
                )
            )
            total_web_evidence += 1

        # Add picture extracts for the claim (Google image search)
        for ir in image_results:
            url = ir.get("url")
            pub = ir.get("displayLink")
            cred = label_credibility(url, pub)
            evidence_items.append(
                EvidenceItem(
                    report_id=report_id,
                    claim_id=claim_id,
                    kind="image_match",
                    url=url or "",
                    publisher=pub,
                    title=ir.get("title"),
                    thumbnail_url=ir.get("thumbnail_url"),
                    credibility=cred,
                )
            )

        reasoned = gemini_rate_claim(report_id, claim_text, evidence_for_reasoner)
        status = (reasoned.get("status") or "Unclear").strip()
        rationale_raw = reasoned.get("rationale")
        rationale = (rationale_raw or "").strip()
        citations_raw = reasoned.get("citations") or []

        # Normalize citations to 1-based integer indices within evidence_for_reasoner.
        citations: list[int] = []
        for c in citations_raw if isinstance(citations_raw, list) else []:
            try:
                i = int(c)
            except Exception:
                continue
            if 1 <= i <= len(evidence_for_reasoner) and i not in citations:
                citations.append(i)

        # Do not inject custom fallback explanations here.
        # If Gemini didn't return a rationale (missing key / empty / failure), leave it empty.

        reasoning_snapshot = {
            "evidence": evidence_for_reasoner,
            "citations": citations,
        }
        has_conflict = False
        if status == "Contradicted":
            has_conflict = True

        confidence = compute_claim_confidence(
            signals=signals,
            corroboration_count=len({(e.get("publisher"), e.get("url")) for e in evidence_for_reasoner if e.get("url")}),
            has_conflict=has_conflict,
        )

        # Update persisted claim
        with get_session() as session:
            persisted = session.get(Claim, claim_id)
            if persisted:
                persisted.status = status
                persisted.confidence = confidence
                persisted.rationale = rationale or None
                persisted.reasoning_json = json.dumps(reasoning_snapshot)
                session.add(persisted)
                session.commit()

        claim_rows.append(
            Claim(
                report_id=report_id,
                claim_text=claim_text,
                status=status,
                confidence=confidence,
                rationale=rationale or None,
                reasoning_json=json.dumps(reasoning_snapshot),
            )
        )

    if report.input_type == InputType.image and report.storage_path:
        # Basic image match lookup based on OCR text; real reverse-image search needs a dedicated service.
        img_query = (claims[0] if claims else "image context")
        img_results = search_images(report_id, img_query, num=6)
        for ir in img_results:
            url = ir.get("url")
            pub = ir.get("displayLink")
            cred = label_credibility(url, pub)
            evidence_items.append(
                EvidenceItem(
                    report_id=report_id,
                    kind="image_match",
                    url=url or "",
                    publisher=pub,
                    title=ir.get("title"),
                    thumbnail_url=ir.get("thumbnail_url"),
                    credibility=cred,
                )
            )

    if total_web_evidence == 0:
        if not google_is_configured():
            missing: list[str] = []
            if not settings.google_cse_api_key:
                missing.append("GOOGLE_CSE_API_KEY")
            if not settings.google_cse_engine_id:
                missing.append("GOOGLE_CSE_ENGINE_ID")

            msg = "No web evidence retrieved because Google Custom Search is not configured."
            if missing:
                msg += " Missing: " + ", ".join(missing) + "."
            msg += " Set these in backend/.env and restart the API."
            limitations.append(msg)
        else:
            limitations.append("No web evidence retrieved for the extracted claims.")
        limitations.append("If results look incomplete, provide more context or a clearer quote fragment.")

    # Determine overall verdict.
    supported = sum(1 for c in claim_rows if c.status == "Supported")
    contradicted = sum(1 for c in claim_rows if c.status == "Contradicted")

    if not claim_rows:
        verdict = Verdict.unverifiable
        overall_conf = 20
        explanation = "No checkable claims were extracted from the input."
    elif contradicted and supported:
        verdict = Verdict.mixed
        overall_conf = int(round(sum(c.confidence for c in claim_rows) / len(claim_rows)))
        explanation = "Some claims are supported while others are contradicted by the retrieved evidence."
    elif contradicted:
        verdict = Verdict.false
        overall_conf = int(round(sum(c.confidence for c in claim_rows) / len(claim_rows)))
        explanation = "Key claims are contradicted by retrieved evidence from listed sources."
    elif supported:
        verdict = Verdict.true
        overall_conf = int(round(sum(c.confidence for c in claim_rows) / len(claim_rows)))
        explanation = "Key claims are supported by retrieved evidence from listed sources."
    else:
        verdict = Verdict.unverifiable
        overall_conf = int(round(sum(c.confidence for c in claim_rows) / len(claim_rows)))
        explanation = "Evidence was insufficient or unclear to verify the extracted claims."

    ai_likelihood = None
    if report.input_type == InputType.image:
        limitations.append("AI-image detection is not enabled in this build, so AI likelihood cannot be determined.")
    if report.input_type == InputType.audio:
        limitations.append("AI-voice detection is not enabled in this build, so AI likelihood cannot be determined.")

    # Origin tracing (best-effort): derive earliest and most likely origin from dated timeline items.
    timeline_items = [t for t in timeline_items if t.get("url")]
    try:
        timeline_sorted = sorted(
            timeline_items,
            key=lambda x: (x.get("date") or "9999-12-31", x.get("source") or ""),
        )
    except Exception:
        timeline_sorted = timeline_items

    earliest = timeline_sorted[0] if timeline_sorted else None
    earliest_appearance = earliest.get("date") if earliest else None
    likely_origin_url = earliest.get("url") if earliest else None

    origin = OriginTrace(
        report_id=report_id,
        likely_origin_url=likely_origin_url,
        earliest_appearance=earliest_appearance,
        timeline_json=json.dumps(timeline_sorted[:30]),
    )

    with get_session() as session:
        for e in evidence_items:
            session.add(e)
        session.add(origin)

        report = session.get(Report, report_id)
        if report:
            report.verdict = verdict
            report.confidence = overall_conf
            report.explanation = explanation
            report.ai_likelihood = ai_likelihood
            # store limitations in audit for now
        session.commit()

    if limitations:
        audit(report_id, "limitations", {"items": limitations})
