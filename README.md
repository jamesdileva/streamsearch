# StreamSearch — Live Event Search Engine

> Find live video about what is happening right now.
> Event-first discovery layer across streaming platforms. Index/discovery only — no video hosting/redistribution.

## Docs (source of truth)

- `docs/architecture.md` — principles, models, API shape
- `docs/implementation-guide.md` — build order, conventions
- `docs/sprint-roadmap.md` — phased verified slices (follow this order)
- `AGENTS.md` — agent working rules, stack, conventions

## Status

Sprint 4.3 done — background refresh (bounded pass over stalest-known-live records: id-reverify → upsert/ended-transition → ended-prune; `POST /api/refresh` manual trigger + opt-out interval loop `REFRESH_*`; unsupported adapters age honestly; no query-discovery crawler). Card-vs-source comparison **deferred** until `YOUTUBE_API_KEY` exists — procedure below stays valid. To smoke-test once you have a key:

```powershell
# backend/.env: YOUTUBE_API_KEY=<key> (never commit it)
python -m uvicorn app.main:app --reload
# then: GET /api/search?q=wildfire  → platform "youtube" records,
# each verifiably live (has actualStartTime). Try: news, wildfire, storm, gaming, concert.
# Confirm per query: results appear, titles/thumbnails match source,
# links open the live broadcast, platform identified, no raw API fields in UI.
```

See `docs/sprint-roadmap.md` (next: 5.1 adapter contract review).

## Target stack

- Frontend: React + Vite + TypeScript
- Backend: Python + FastAPI
- Storage (PoC): SQLite
- Search (MVP): deterministic scoring; FTS later; embeddings only if proven needed
- Cache (MVP): in-memory short-lived server cache

## Quickstart

```powershell
# backend (from backend/)
# copy ../.env.example to .env first, fill keys
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://localhost:8000/api/health

# frontend (from frontend/)
# copy .env.example to .env (VITE_API_URL=http://localhost:8000)
npm install
npm run dev                               # http://localhost:5173
```

## Checks (Sprint 0.1 toolchain — enforced)

```powershell
# backend (from backend/)
python -m pytest -q
python -m ruff check .

# frontend (from frontend/)
npm run typecheck   # tsc --noEmit
npm run lint        # oxlint
npm run test        # vitest run
npm run build
```

- Backend health: `GET /api/health`
- Search: `GET /api/search?q=wildfire` → `{query, results[], count}`
- Never commit `.env`. Never expose API keys in frontend.

## MVP done when

User can open site → search topic/event → get normalized YouTube results → see live/freshness + source/creator → watch via embed or open source → report bad results → repeat searches without excessive API use.
