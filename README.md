# Wikipedia Analysis (Word Frequencies + Word Cloud)

## Tech stack

- **Python** 🐍
- **FastAPI** ⚡️
- **React** ⚛️

I built this project to explore how quickly I can turn a small analysis idea into a working web app by pairing with an agent inside Windsurf.

At a high level, this app:

- Pulls page content from a Wikipedia category via the MediaWiki API.
- Tokenizes the text, filters common stopwords, and computes word counts.
- Caches results on disk so repeated runs are fast.
- Serves the results via a FastAPI backend.
- Visualizes the results in a React (Vite) frontend as a word cloud.

## What I’m exploring (Windsurf + agentic coding)

I’m using Windsurf as my “workbench” for building small apps:

- I describe the feature I want.
- The agent helps me design a clean interface, implement endpoints/components, and iterate quickly.
- I still stay in control of the codebase and can refactor to keep it production-quality.

This repo is intentionally simple, but it’s structured so that I can keep scaling it.

## Project layout

- `category_wordfreq.py`
  - Core logic for fetching Wikipedia pages and computing word counts.
  - Writes cache files under `.cache/`.
- `backend/`
  - FastAPI app that exposes an API for the frontend.
- `frontend/`
  - React + Vite UI.
  - Uses a dev proxy so the frontend can call the backend at `/api/*` without CORS issues.

## Caching

Results are cached under:

- `.cache/category_<CategoryName>.json`

The backend will use the cache if available, otherwise it recomputes and writes a new cache file.

## Backend (FastAPI)

### Install

```bash
pip3 install -r requirements.txt
```

### Run

From the repo root:

```bash
python3 -m uvicorn backend.main:app --reload --port 8000
```

### Local endpoints

- `GET http://127.0.0.1:8000/api/wordfreq`

Example:

```text
http://127.0.0.1:8000/api/wordfreq?category=Large_language_models&metric=count&top=200&min_count=2
```

Query parameters:

- `category` (required)
- `metric`: `count` or `freq` (default: `count`)
- `top`: max number of words to return (default: `200`)
- `min_count`: filter out low-count words (default: `1`)
- `refresh`: `true` to ignore cache and recompute (default: `false`)
- `sleep`: seconds to sleep between API calls when recomputing (default: `0.0`)

## Frontend (React + Vite)

### Install

This repo is set up so **Node dependencies live under `frontend/`**.

From the repo root:

```bash
npm --prefix frontend install
```

### Run

From the repo root:

```bash
npm run dev
```

### Local URLs

- Frontend: `http://localhost:5173/`
- Backend API (direct): `http://127.0.0.1:8000/api/wordfreq?...`
- Frontend-to-backend (via dev proxy): `http://localhost:5173/api/wordfreq?...`

## Typical workflow

In two terminals:

### Terminal 1 (backend)

```bash
python3 -m uvicorn backend.main:app --reload --port 8000
```

### Terminal 2 (frontend)

```bash
npm --prefix frontend install
npm run dev
```

Then open:

- `http://localhost:5173/`

## Notes

- If you see a `Failed to fetch` error in the frontend, I first check that the backend is running and then restart the Vite dev server. The UI calls `/api/...` and relies on Vite’s proxy configuration.

