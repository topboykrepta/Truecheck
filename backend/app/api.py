from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.db import get_session
from app.models import AuditEvent, InputType, Report, ReportStatus
from app.schemas import AuditResponse, ReportResponse, UploadResponse
from app.services.audit import audit
from app.services.pipeline import run_pipeline
from app.services.queue import enqueue_report


router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "truecheck-api", "time": datetime.utcnow().isoformat()}


@router.post("/upload/text", response_model=UploadResponse)
async def upload_text(payload_text: str = Form(...), background: BackgroundTasks = None):
    if background is None:
        background = BackgroundTasks()

    report_id = str(uuid.uuid4())

    with get_session() as session:
        report = Report(
            id=report_id,
            input_type=InputType.text,
            input_text=payload_text,
            status=ReportStatus.queued,
        )
        session.add(report)
        session.commit()

    audit(report_id, "upload", {"input_type": "text"})

    if settings.truecheck_use_queue:
        enqueued = enqueue_report(report_id)
        if not enqueued:
            background.add_task(run_pipeline, report_id)
    else:
        background.add_task(run_pipeline, report_id)

    return UploadResponse(report_id=report_id, status="queued")


@router.post("/upload/file", response_model=UploadResponse)
async def upload_file(
    input_type: str = Form(...),
    file: UploadFile = File(...),
    background: BackgroundTasks = None,
):
    if background is None:
        background = BackgroundTasks()

    if input_type not in ("image", "audio", "text"):
        raise HTTPException(status_code=400, detail="input_type must be text|image|audio")

    report_id = str(uuid.uuid4())
    storage_dir = Path(settings.truecheck_storage_dir) / report_id
    storage_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "upload"
    dest = storage_dir / filename

    with dest.open("wb") as f:
        f.write(await file.read())

    with get_session() as session:
        report = Report(
            id=report_id,
            input_type=InputType(input_type),
            original_filename=filename,
            storage_path=str(dest),
            status=ReportStatus.queued,
        )
        session.add(report)
        session.commit()

    audit(report_id, "upload", {"input_type": input_type, "filename": filename})

    if settings.truecheck_use_queue:
        enqueued = enqueue_report(report_id)
        if not enqueued:
            background.add_task(run_pipeline, report_id)
    else:
        background.add_task(run_pipeline, report_id)

    return UploadResponse(report_id=report_id, status="queued")


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: str):
    from app.services.reports import build_report_response

    return build_report_response(report_id)


@router.get("/reports/{report_id}/audit", response_model=AuditResponse)
def get_audit(report_id: str):
    from app.services.reports import build_audit_response

    return build_audit_response(report_id)
