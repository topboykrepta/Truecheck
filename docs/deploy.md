# Deploy (Simple)

This repo is designed to deploy cleanly to most platforms:

- **Backend API** (FastAPI) to any Python hosting/PaaS (Render/Railway/Fly/Heroku-like)
- **Frontend** (static HTML/CSS/JS) to any static host (Netlify recommended)

## 1) Push to GitHub

From the repo root:

```powershell
Set-Location "c:\Users\Administrator\OneDrive\Desktop\All\TrueCheck"

# init (only once)
git init

git add .

git commit -m "Initial TrueCheck deployment"
```

Create a new GitHub repo (empty), then add the remote + push:

```powershell
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Important:
- Do **not** commit secrets. `backend/.env` is ignored by `.gitignore`.

## 2) Deploy backend API (any platform)

Deploy the `backend/` folder as a Python web service. A `backend/Procfile` is included for platforms that support it.

Set these environment variables in your hosting platform (do not commit them):

- `GOOGLE_CSE_API_KEY` = your Google Custom Search API key
- `GOOGLE_CSE_ENGINE_ID` = your Programmable Search Engine ID
- `GEMINI_API_KEY` = your Gemini API key (optional but recommended)
- `GEMINI_MODEL` = `gemini-2.0-flash` (or your chosen model)

Server behavior:
- `TRUECHECK_USE_QUEUE` = `0` (recommended on serverless)
- `TRUECHECK_CORS_ORIGINS` = `https://<your-netlify-site>.netlify.app`

Your API should be available at:

- `https://<your-api-host>/api/v1/health`

## 3) Deploy frontend to Netlify

- Import the same GitHub repo in Netlify
- Netlify will use `netlify.toml`:
  - publish directory: `frontend/`
  - build command: none (static files)
  - SPA fallback redirect to `/index.html`

Deploy.

## 4) Quick test checklist

- Open the Netlify site
- Submit a text claim
- Verify:
  - Evidence shows `web_extracts` and `image_matches`
  - Thumbnails appear when Google returns them
  - Each claim shows a per-claim rationale when Gemini is configured

## Connecting frontend → backend

By default, the frontend assumes the API is on **the same origin** at `/api/v1` in production.

Options:
- If you want the frontend to call your backend directly, update `frontend/app.js` (or set up an API proxy via your host).
- If you want a same-origin experience on Netlify, add a Netlify redirect that proxies `/api/v1/*` to your API host.
