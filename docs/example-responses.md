# Example Responses

## Text input

```json
{
  "report_id": "4c3a...",
  "created_at": "2026-02-07T12:00:00Z",
  "updated_at": "2026-02-07T12:00:10Z",
  "input_type": "text",
  "status": "complete",
  "verdict": "Unverifiable",
  "confidence": 34,
  "ai_likelihood": null,
  "explanation": "Evidence was insufficient or unclear to verify the extracted claims.",
  "key_claims": [
    {
      "claim_text": "X happened on Y date.",
      "status": "Unclear",
      "confidence": 34,
      "citations": [
        {
          "url": "https://example.com/article",
          "publisher": "example.com",
          "date": "2026-02-05",
          "snippet": "...",
          "credibility": "Neutral"
        }
      ]
    }
  ],
  "evidence": {
    "web_extracts": [],
    "image_matches": [],
    "trusted_sources": []
  },
  "origin_tracing": {
    "most_likely_origin_urls": [],
    "earliest_appearance": null,
    "timeline": []
  },
  "limitations": [
    "Google Custom Search API not configured; no web evidence retrieved."
  ]
}
```

## Image input

- Same structure, plus `ai_likelihood` (if enabled) and `image_matches` entries.

## Audio input

- Same structure, plus a limitation if transcription is not configured.
