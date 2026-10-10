# StreamSearch — Live Event Search Engine

> Find live video about what is happening right now.
> Event-first discovery layer across streaming platforms. Index/discovery only — no video hosting/redistribution.

## Docs (source of truth)

- `docs/architecture.md` — principles, models, API shape
- `docs/implementation-guide.md` — build order, conventions
- `docs/sprint-roadmap.md` — phased verified slices (follow this order)
- `AGENTS.md` — agent working rules, stack, conventions

## Status

Sprint 7.1 done — keyword-insufficiency benchmark (`backend/benchmarks/failure_dataset.py`, run via `python -m benchmarks.failure_dataset`).

Sprint 7.2b done — embedding bake-off (`python -m benchmarks.embedding_experiment`): 4 local models, keyword 3/8 → semantic 4–5/8 with identical failures across 137M–567M models (bge-m3 best at 5/8, one case).

Sprint 7.3 done — **hybrid ranking decided: NOT adopted.** The only case semantics fixed is closed instead by keyword weight `description` 15→25. Benchmark now **4/8** (4 controls pass, 4 gaps remain pinned). `embeddings.py` stays experimental and unwired for cheap re-runs.

Dual-platform live verification **deferred** until both credentials exist. To smoke-test once you have them:

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

Sprint 10.2 done - rate limiting + abuse protection: in-memory sliding-window limiter (search 60/min, refresh 2/5min, per-peer, X-Forwarded-For deliberately ignored, unknown scopes fail open), query validation (200 chars, control chars, repeated filler) with privacy-safe logging (length + digest, never raw input), and 429/422 error envelopes.

Sprint 12.1 done — TikTok feasibility: **NO-GO** (no official live-discovery API; all access undocumented). See `docs/tiktok-feasibility.md`.

Sprint 13.1 done — transcript relevance: **NO-GO** in `docs/transcript-relevance.md`. `captions.download` requires OAuth 2.0 and owner-level edit permission, so transcripts of third-party streams (what a discovery engine needs) aren't legitimately accessible; `captions.list`+download also cost 250 units/stream. Undocumented caption endpoints stay out of bounds. `vague-title` gap stays open and labelled unclosable legitimately. Remaining Phase 13 experiments: 13.2 event detection, 13.3 CV (also expected NO-GO).

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
