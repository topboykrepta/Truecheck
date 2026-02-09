# Safety, Compliance, Robustness

## Prompt injection defenses

- Treat uploaded content and web snippets as **untrusted data**.
- Sanitize and truncate snippets before sending to Gemini.
- Use strict instruction hierarchy: system rules > developer rules > user content.
- Require strict JSON outputs from Gemini and ignore anything else.

## Privacy

- Redact common PII-like patterns from evidence snippets stored/returned.
- Do not attempt to identify private individuals.
- In production, restrict logging of raw uploads; store hashes/redacted excerpts.

## Auditability

- Every report records:
  - searches that ran
  - integrations used/skipped
  - errors and limitations

## Error handling

- If evidence APIs fail or rate limit, complete the report with limitations and avoid guessing.

## Disclaimer

TrueCheck provides assistance, not absolute authority.
