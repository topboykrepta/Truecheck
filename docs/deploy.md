# Deploy (Vercel API + Netlify Web)

This repo is set up to deploy:

- **Backend API** (FastAPI) to **Vercel** as a Python Serverless Function
- **Frontend** (static HTML/CSS/JS) to **Netlify**

The frontend calls `/api/v1/...` on the same origin, and Netlify proxies that to your Vercel API.

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

## 2) Deploy backend to Vercel

### A) Create Vercel project

- Import the GitHub repo in Vercel
- Choose **Project Name**: `truecheck-api` (so Netlify proxy works without edits)

### B) Set Environment Variables (Vercel Project Settings → Environment Variables)

Set these values in Vercel (do not commit them):

- `GOOGLE_CSE_API_KEY` = your Google Custom Search API key
- `GOOGLE_CSE_ENGINE_ID` = your Programmable Search Engine ID
- `GEMINI_API_KEY` = your Gemini API key (optional but recommended)
- `GEMINI_MODEL` = `gemini-2.0-flash` (or your chosen model)

Server behavior:
- `TRUECHECK_USE_QUEUE` = `0` (recommended on serverless)
- `TRUECHECK_CORS_ORIGINS` = `https://<your-netlify-site>.netlify.app`

Deploy. Your API should be available at:

- `https://truecheck-api.vercel.app/api/v1/health`

## 3) Deploy frontend to Netlify

- Import the same GitHub repo in Netlify
- Netlify will use `netlify.toml`:
  - publish directory: `frontend/`
  - build command: none (static files)
  - SPA fallback redirect to `/index.html`
  - proxy redirect: `/api/v1/*` → `https://truecheck-api.vercel.app/api/v1/*`

Deploy.

## 4) Quick test checklist

- Open the Netlify site
- Submit a text claim
- Verify:
  - Evidence shows `web_extracts` and `image_matches`
  - Thumbnails appear when Google returns them
  - Each claim shows a per-claim rationale when Gemini is configured

## If you did NOT name the Vercel project `truecheck-api`

Edit `netlify.toml` and replace:

- `https://truecheck-api.vercel.app` → `https://<your-vercel-project>.vercel.app`

Then push and redeploy Netlify.
