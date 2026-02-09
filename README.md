# TrueCheck

TrueCheck is a misinformation, disinformation, and AI-generated content detection system.

This repo contains:
- `backend/`: FastAPI API server + DB models
- `backend/worker/`: RQ worker that runs analysis jobs
- `frontend/`: static HTML/CSS/JS UI
- `docs/`: architecture, API design, data models, scoring rules, examples

## Quickstart (dev)

### 1) Backend API

1. Copy env template:
   - `copy backend\.env.example backend\.env`
2. Create a venv and install deps:
   - `cd backend`
   - `python -m venv .venv`
   - `./.venv/Scripts/pip install -r requirements.txt`
3. Run the API:
   - `./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000`

Health check: `http://localhost:8000/api/v1/health`

### 2) Worker (optional but recommended)

TrueCheck uses Redis + RQ for a real worker queue.

- Start Redis (example using Docker):
  - `docker run -p 6379:6379 redis:7`
- In another terminal:
  - `cd backend`
  - `./.venv/Scripts/python -m worker.worker`

If Redis is not available, the API falls back to in-process background execution.

### 3) Frontend

Serve the static frontend (any static server works):

- `cd frontend`
- `python -m http.server 5173`

Open: `http://localhost:5173`

Configure the API base URL in `frontend/app.js` if needed.

## Documentation

- `docs/architecture.md`
- `docs/api.md`
- `docs/data-models.md`
- `docs/scoring.md`
- `docs/security.md`
- `docs/example-responses.md`
- `docs/implementation-plan.md`

## Notes

- External integrations (Google Custom Search / Image Search, Gemini) are optional at runtime.
- TrueCheck never “invents” sources: the reasoning layer can only cite retrieved evidence.

## External API setup

- **Google Programmable Search (Custom Search Engine)**
   - Set `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ENGINE_ID` in `backend/.env`
   - Used for:
      - web corroboration (`search_web`)
      - image matches (`search_images`)

- **Gemini**
   - Set `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) in `backend/.env`
   - TrueCheck sends Gemini only the retrieved evidence snippets and requires strict JSON output.

- **GDELT (optional, no key)**
   - Enabled by default as an additive evidence source for web/news corroboration.

### Security note

- Do **not** commit `backend/.env` to source control. This repo includes `.gitignore` rules to help prevent accidental commits.
