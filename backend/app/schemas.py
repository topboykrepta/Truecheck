from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class UploadTextRequest(BaseModel):
    input_type: str = Field(default="text")
    text: str


class UploadResponse(BaseModel):
    report_id: str
    status: str


class Citation(BaseModel):
    url: str
    publisher: Optional[str] = None
    date: Optional[str] = None
    snippet: Optional[str] = None
    credibility: Optional[str] = None


class ClaimRow(BaseModel):
    claim_text: str
    status: str
    confidence: int
    rationale: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)


class EvidenceWebExtract(BaseModel):
    url: str
    publisher: Optional[str] = None
    date: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    credibility: Optional[str] = None


class EvidenceImageMatch(BaseModel):
    url: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    credibility: Optional[str] = None


class OriginItem(BaseModel):
    date: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    context: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    created_at: datetime
    updated_at: datetime
    input_type: str
    status: str

    verdict: Optional[str] = None
    confidence: Optional[int] = None
    ai_likelihood: Optional[int] = None
    explanation: Optional[str] = None

    key_claims: list[ClaimRow] = Field(default_factory=list)

    evidence: dict[str, Any] = Field(default_factory=dict)
    origin_tracing: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class AuditResponse(BaseModel):
    report_id: str
    events: list[dict[str, Any]]
