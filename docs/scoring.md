# Scoring Logic

TrueCheck uses **deterministic, explainable scoring** and (optionally) a Gemini reasoning layer.

## Deterministic (rules-based)

For each claim:

1. **Evidence quality weighting**
   - Trusted: 1.0
   - Neutral: 0.8
   - Unknown: 0.5
   - Low credibility: 0.2

2. **Freshness weighting**
   - Newer items get slightly higher weight; very old items decay.

3. **Corroboration weighting**
   - Multiple independent sources adds up to +0.15 total boost.

4. **Conflict handling**
   - If the claim is contradicted, apply a penalty (default 0.25).

Final claim score is mapped to 0–100.

## Gemini-assisted reasoning (optional)

- Gemini receives:
  - the claim
  - a list of evidence snippets/URLs
- Output must be JSON:
  - `status`: Supported|Contradicted|Unclear
  - `rationale`
  - `citations`: indices into the provided evidence list

**Hard rule**: Gemini cannot introduce new sources; it can only cite the evidence objects provided.

## Overall verdict

- Supported majority -> `True`
- Contradicted majority -> `False`
- Mixed supported + contradicted -> `Mixed`
- No strong evidence -> `Unverifiable`
- Image/audio AI likelihood can produce `AI-Generated` verdict if enabled and strong.
