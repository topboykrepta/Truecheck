# System Architecture

## High-level

- **Frontend**: Static HTML/CSS/JS app (`frontend/`) that uploads content and renders a structured verification report.
- **Backend API**: FastAPI (`backend/app/`) provides upload endpoints, job status/report retrieval, and audit logs.
- **Worker Queue**: Redis + RQ (`backend/worker/`) runs analysis asynchronously (OCR, transcription, search, scoring, Gemini reasoning).
- **Database**: SQL (default SQLite for dev; Postgres recommended for production) stores reports, claims, evidence items, and audit events.
- **Storage**: Local storage directory for uploaded files in dev; in production use object storage (S3/GCS/Azure Blob).

## Data flow

1. User uploads text/image/audio via the frontend.
2. API persists a `Report` + stores the file (if any).
3. API enqueues `report_id` onto the queue.
4. Worker loads the report, runs the pipeline:
   - Text: claim extraction -> web corroboration -> scoring -> verdict
   - Image: OCR -> claim extraction -> web corroboration + image search -> scoring -> verdict
   - Audio: transcription -> claim extraction -> web corroboration -> scoring -> verdict
5. API serves the completed report to the frontend.

## Components

- **Claim extraction (deterministic)**: Rules-based splitter produces checkable statements.
- **Evidence retrieval**:
  - Web results: Google Custom Search API
  - Image matches: Google Programmable Search (searchType=image)
- **Credibility labeling**: Domain-based trusted/neutral/unknown/low (transparent and configurable).
- **Scoring**: Deterministic, explainable rules; Gemini can refine per-claim rationale but cannot add sources.
- **Audit log**: Records searches, integrations used/skipped, failures, and limitations.

## Production notes

- Run API behind a reverse proxy (nginx) with TLS.
- Run worker(s) separately; scale horizontally.
- Add persistent cache layer for search results; use TTL to control cost.
- Add rate limiting per IP/API key.
