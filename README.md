# TrustCheck PK

Single Vercel project: **React (Vite) frontend** + **Python (FastAPI) backend** + **Supabase**.

```
trustcheck-pk/
├── frontend/          # React + Vite (Vercel frontend service)
├── backend/           # FastAPI + Supabase (Vercel backend service)
├── supabase/          # SQL schema
├── vercel.json        # Services + routing for one-click deploy
├── PROMPTS.md
└── README.md
```

## Deploy on Vercel (complete app)

This project deploys as **one FastAPI app** on Vercel. The build step compiles the React frontend, and FastAPI serves both the UI and `/api/*`.

1. Push this repo to GitHub.
2. In [vercel.com](https://vercel.com) → **Add New Project** → import the repo.
3. Framework should be **FastAPI** (see `vercel.json` / `pyproject.toml`).
4. Add Environment Variables (Production + Preview):

| Name | Value |
|---|---|
| `SUPABASE_URL` | your Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | your publishable key |

5. Deploy. Open the live URL — UI is at `/`, API at `/api/...`.

6. In Vercel → Settings → Deployment Protection, turn **off** “Vercel Authentication” for Production so the public demo/API works.

## Supabase setup (once)

Run [`supabase/schema.sql`](supabase/schema.sql) in the Supabase SQL Editor.

## Local development

```bash
# terminal 1 — API
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill Supabase keys
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# terminal 2 — UI
cd frontend
npm install
npm run dev
```

Open http://localhost:5173  
Vite proxies `/api` → `http://127.0.0.1:8000`.

Or from repo root:

```bash
npm run dev:backend
npm run dev
```

## Security

- Supabase keys live only in backend / Vercel env vars
- Frontend never imports Supabase
- Frontend calls same-origin `/api/*` only
