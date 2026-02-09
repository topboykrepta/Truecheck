# Implementation Plan (Milestones)

## Milestone 1 — MVP skeleton (this repo)

- Upload + report retrieval
- Background pipeline (RQ worker)
- Deterministic claim extraction + scoring
- Evidence retrieval via Google CSE (optional)
- Gemini reasoning wired but optional
- UI renders report sections + audit log

## Milestone 2 — Evidence depth

- Better entity extraction and query expansion
- Per-claim citation mapping
- Better origin tracing (earliest indexed occurrences)
- Cache search results + de-duplication

## Milestone 3 — Image verification

- Strong reverse image search integration (provider-dependent)
- Perceptual hashing for near-duplicate detection
- AI-image detection model integration (with calibration)

## Milestone 4 — Audio verification

- Robust transcription + diarization
- AI-voice detector integration (model + calibration)
- Timestamped claim highlights linked to transcript

## Milestone 5 — Production hardening

- Postgres + migrations
- Auth (optional) + API keys
- Rate limiting, abuse detection
- Observability: metrics, tracing, dashboards
- Cost controls: quotas, caching, batching
