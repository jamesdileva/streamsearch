# StreamSearch — Live Event Search Engine

> Find live video about what is happening right now.
> Event-first discovery layer across streaming platforms. Index/discovery only — no video hosting/redistribution.

## Docs (source of truth)

- `docs/architecture.md` — principles, models, API shape
- `docs/implementation-guide.md` — build order, conventions
- `docs/sprint-roadmap.md` — phased verified slices (follow this order)
- `AGENTS.md` — agent working rules, stack, conventions

## Status

Sprint 5.3 done — unified cross-platform results (one ranked set, no platform term in scoring; server-side `platform` / `sort=relevance|newest|viewers` / `has_location` params; `SearchFilters` UI with platform options derived from live results; filter variants get separate cache entries). Dual-platform live verification **deferred** until both credentials exist. To smoke-test once you have them:

```powershell
# backend/.env (never commit it):
# YOUTUBE_API_KEY=<key>
# TWITCH_CLIENT_ID=<id>
# TWITCH_CLIENT_SECRET=<secret>
# TWITCH_EMBED_PARENT=localhost  # production: your frontend host
python -m uvicorn app.main:app --reload
# then: GET /api/search?q=wildfire  → platform "youtube" + "twitch" records
# in one ranked set. Try topics with both-platform coverage (news, gaming,
# concert). Confirm per query: results appear, titles/thumbnails match
# source, links open the live broadcast, platform identified, no raw API
# fields in UI, and neither platform dominates every query.
# Also try: &platform=twitch, &sort=viewers, &sort=newest,
# &has_location=true — filters combine with the query server-side.
```

See `docs/sprint-roadmap.md` (next: 6.1 event vs. stream data model).

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
