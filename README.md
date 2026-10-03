# StreamSearch — Live Event Search Engine

> Find live video about what is happening right now.
> Event-first discovery layer across streaming platforms. Index/discovery only — no video hosting/redistribution.

## Docs (source of truth)

- `docs/architecture.md` — principles, models, API shape
- `docs/implementation-guide.md` — build order, conventions
- `docs/sprint-roadmap.md` — phased verified slices (follow this order)
- `AGENTS.md` — agent working rules, stack, conventions

## Status

Sprint 0.1 — bootstrapping. See `docs/sprint-roadmap.md`.
No `frontend/` / `backend/` yet.

## Target stack

- Frontend: React + Vite + TypeScript
- Backend: Python + FastAPI
- Storage (PoC): SQLite
- Search (MVP): deterministic scoring; FTS later; embeddings only if proven needed
- Cache (MVP): in-memory short-lived server cache

## Quickstart (after Sprint 0.1 scaffold)

```powershell
# backend (from backend/)
# copy ../.env.example to .env first, fill keys
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (from frontend/)
npm install
npm run dev
```

- Backend health: `GET /api/health`
- Search: `GET /api/search?q=wildfire` → `{query, results[], count}`
- Never commit `.env`. Never expose API keys in frontend.

## MVP done when

User can open site → search topic/event → get normalized YouTube results → see live/freshness + source/creator → watch via embed or open source → report bad results → repeat searches without excessive API use.
