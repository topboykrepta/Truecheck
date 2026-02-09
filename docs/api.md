# API Design

Base: `/api/v1`

## Health

- `GET /health` -> `{ ok: true }`

## Upload

### Text

- `POST /upload/text` (form)
  - `payload_text`: string
- Response:
  - `{ report_id, status }`

### File (image/audio/text document)

- `POST /upload/file` (multipart)
  - `input_type`: `image|audio|text`
  - `file`: upload
- Response:
  - `{ report_id, status }`

## Report retrieval

- `GET /reports/{report_id}`
  - Returns structured report:
    - Summary (verdict/confidence/aiLikelihood/explanation)
    - Key claims with per-claim status + citations
    - Evidence gallery (web extracts, image matches, trusted sources)
    - Origin tracing (URLs, earliest appearance, timeline)
    - Limitations

## Audit

- `GET /reports/{report_id}/audit`
  - Returns ordered list of analysis steps:
    - searches run
    - integrations configured/skipped
    - errors/limitations

## Error handling

- `400`: invalid upload
- `404`: report not found
- `429`: rate limit (recommended enhancement)
- `5xx`: integration failures handled gracefully; report may be `failed` or `complete` with limitations
