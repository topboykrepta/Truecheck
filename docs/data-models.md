# Data Models

## Report

- `id` (UUID)
- `input_type`: text|image|audio
- `status`: queued|running|complete|failed
- `verdict`: True|False|Misleading|Unverifiable|AI-Generated|Mixed
- `confidence`: 0–100
- `ai_likelihood`: 0–100 (optional)
- `explanation`: short paragraph
- `input_text` or `storage_path`
- timestamps

## Claim

- `report_id`
- `claim_text`
- `status`: Supported|Contradicted|Unclear
- `confidence`: 0–100

## EvidenceItem

- `kind`: web_extract|image_match
- `url`, `publisher`, `published_date`
- `title`, `snippet`
- `thumbnail_url` (for images)
- `credibility`: Trusted|Neutral|Unknown|Low credibility

## OriginTrace

- `likely_origin_url`
- `earliest_appearance`
- `timeline_json`: list of {date, source, url, context}

## AuditEvent

- `event_type`: upload|enqueue|web_search|image_search|gemini_call|... etc
- `details_json`: structured payload
