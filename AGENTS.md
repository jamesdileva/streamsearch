# AGENTS.md â€” Live Event Search Engine (StreamSearch)

> Event-first live discovery layer: "Find live video about what is happening right now."
> Index/discovery only. Do NOT download, host, or re-distribute source video. Prefer official APIs, embeds, and external links.

Source of truth for product/architecture:
- `docs/architecture.md` â€” principles, tech choices, models, API shape
- `docs/implementation-guide.md` â€” build order, conventions, gates
- `docs/sprint-roadmap.md` â€” phased verified vertical slices (follow this order)

## 1. Stack (do not change without explicit approval)

- Frontend: React + Vite + TypeScript, responsive grid/list UI. Lightweight CSS/component approach.
- Backend: Python + FastAPI. This is an API/search service; Python preserves future NLP/embedding option.
- Storage (PoC): SQLite. Later: PostgreSQL. No Postgres/Redis infra until justified.
- Search (MVP): deterministic scoring over stored fields. Later: SQLite FTS5 / Postgres FTS. Embeddings/vector search ONLY after `sprint-roadmap.md 7.1` failure dataset proves keyword search insufficient.
- Caching (MVP): in-memory + short-lived server cache keyed by normalized query. Redis only if traffic/polling justifies it.

Toolchain (locked in Sprint 0.1, enforce every sprint):
- Frontend (from `frontend/`): `npm run dev`, `npm run build`, `npm run lint` (oxlint), `npm run test` (vitest), `npm run typecheck` (`tsc --noEmit`)
- Backend (from `backend/`): `python -m uvicorn app.main:app --reload`, `python -m pytest -q`, `python -m ruff check .` (use `python -m` prefix if shims aren't on PATH; no black â€” `ruff` only)

## 2. Target repo layout

```text
./
â”œâ”€â”€ frontend/            # React+Vite+TS (src/components, pages, services, types, App.tsx)
â”œâ”€â”€ backend/             # FastAPI (app/api, app/adapters, app/models, app/search, app/services, app/config.py, app/main.py + tests/)
â”œâ”€â”€ docs/                # architecture.md, implementation-guide.md, sprint-roadmap.md
â”œâ”€â”€ AGENTS.md
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example
â””â”€â”€ .gitignore
```

Current state: Phase 13 complete. 13.2 event detection: works on live data (`GET /api/events?q=` prototype, NOT wired to search) — recall 2/2 and precision 5/5 on the labeled set, and on live YouTube the `storm` query grouped all 10 Hurricane Isaias broadcasts into one event with no false merges afterwards; verdict is "keep prototype, don't ship as a ranking feature" pending a larger sample (`docs/event-detection.md`). 13.3 CV: **NO-GO without an experiment** — decoding frames violates the enforced metadata-only boundary of §11.1, and small-VLM reliability plus GPU/cost make it unaffordable. Formatter/linter choices locked: backend `ruff`, frontend `oxlint`; backend run via `python -m` if shims are not on PATH.

## 3b. Sprint loop (mandatory for every sprint)

For every sprint do in order: `plan â†’ scope â†’ implement â†’ verify â†’ commit â†’ worklog â†’ push`.

1. Plan â€” read the roadmap sprint. State Goal / Work / Non-goals / Verification. Create todo list.
2. Scope â€” one vertical slice only. List files to touch. No drive-by refactors or next-sprint work.
3. Implement â€” code + minimal docs updates. Respect Â§4â€“Â§6 (adapters, normalized model, quota/security).
4. Verify (tests) â€” run relevant checks and record results:
   - Backend (if touched): `pytest`, `ruff check .`
   - Frontend (if touched): `npx tsc --noEmit`, `npm run lint`, `npm run test`
   - Manual checklist from roadmap sprint (e.g. 5 queries, states, failure injection). Real platform APIs only for controlled smoke tests; mocks otherwise.
   - If checks fail, fix before committing.
5. Commit â€” Conventional Commits with sprint ref (e.g. `feat: sprint 0.1 frontend shell + health wiring`). One logical commit per sprint unless split is justified.
6. Worklog â€” append to `worklog.md`: date, sprint, branch, what changed, verification run + result, commit hash. Keep it append-only, newest at bottom.
7. Push â€” push branch, merge to `main`, push `main` (see Â§8). If no GitHub remote yet, create with `gh repo create streamsearch` (confirm private/public first), then push.

## 3. How to work (mandatory)

1. Follow `sprint-roadmap.md` order strictly:
   `FOUNDATION â†’ YOUTUBE â†’ REAL SEARCH â†’ FRESHNESS â†’ RELEVANCE â†’ LOCATION â†’ CACHE/INDEX â†’ TWITCH â†’ CROSS-PLATFORM â†’ EVENT MODEL â†’ SEMANTIC EXPERIMENT â†’ KICK â†’ OPTIONAL â†’ TIKTOK EXPERIMENT`
   Do NOT build AI, maps, 5 adapters, event clustering, accounts, alerts, or CV before the basic YouTube search loop is proven.
2. One vertical slice at a time. One platform at a time (YouTube first). Each slice must have Goal / Work / Verification / End state.
3. Verification philosophy per feature â€” answer: Does it work? Is it accurate vs. source truth? Is it useful for real queries (e.g. `wildfire`, `storm`, `news`, `concert`)? Does it scale reasonably (API calls, latency, cache hits)?
4. Run relevant checks before finishing: backend `pytest` + `ruff`, frontend `tsc --noEmit` + `lint` + `test`. Mock platform responses for automated tests; use real API calls only for controlled smoke tests.
5. Keep diffs small and platform-agnostic. Never commit secrets (see Â§6).

## 4. Backend conventions

- Adapters live ONLY in `backend/app/adapters/` (`base.py` interface + `youtube.py`, `twitch.py`, â€¦).
  Adapter contract: receive normalized search request â†’ call platform â†’ map to common Stream model â†’ return controlled errors. Search/business logic must NEVER import YouTube/Twitch response shapes.
- Normalized Stream fields (superset, keep platform extras in `metadata`): `id, platform, platform_stream_id, channel_id, channel_name, title, description, thumbnail_url, source_url, embed_url, embed_supported, live_status, started_at, discovered_at, last_verified_at, viewer_count, category, tags, latitude, longitude, location_text, metadata`.
- API shape (MVP):
  `GET /api/search?q={query}` â†’ `{query, results[], count}` (+ later `platform status` for partial results)
  `GET /api/streams/{id}`, `GET /api/health`, `POST /api/reports`
- Relevance: isolated, configurable scoring function. Conceptual weights: title exact/token high, location high, description/category/tag medium, freshness medium, viewer_count low (never primary). No hardcoded weights scattered in code.
- Freshness is first-class: maintain `discovered_at, last_verified_at, started_at, ended_at`. Thresholds: Fresh / Aging / Stale / Ended. Never leave a stream marked LIVE forever from one old response; revalidate periodically.
- Failure isolation: timeout, quota errors, empty results, stale live flags, outages. One platform failure must NOT fail the whole search â€” return partial results + per-platform status.
- Config via env only: `YOUTUBE_API_KEY, DATABASE_URL, APP_ENV`. See `.env.example`.

## 5. Frontend conventions

- Consume ONLY normalized API responses. No platform-specific parsing in UI.
- Small components: `SearchBar, SearchFilters, ResultsGrid, StreamCard, PlatformBadge, LiveStatus, SourceButton, ReportButton`. Keep playback isolated from discovery.
- Primary UX copy: `What are you looking for happening live?` Search on submit/debounced â€” never per-keystroke API fan-out.
- Cards must show: live/freshness indicator, title, creator/channel, platform, thumbnail, start time, viewers (if available), location (if available), `[Watch]` (if embed allowed) + `[Open Source]`.
- States required: loading, empty, error, responsive mobile/desktop.

## 6. Security, quota, legal (non-negotiable)

- Never expose API keys in frontend. Never commit `.env`. Validate/sanitize all search input. Rate-limit backend. Do NOT proxy arbitrary URLs. Treat all platform metadata as untrusted.
- YouTube search quota is expensive: normalize queries, short-lived server cache, request budgets, debounced submit. Measure `cache hit/miss, API request count, error count`.
- Respect platform ToS, robots/technical restrictions, copyright, embed policies. Use documented/legitimate access only. Store only discovery metadata, never video. Preserve source attribution. Support `Report Broken / No Longer Live / Wrong Topic / Other` (`POST /api/reports`).
- No new platform until prior adapter is stable + normalized records work + relevance measurable + staleness handled + failure isolation proven. Kick/TikTok/X require feasibility doc first â€” scraping is NOT assumed acceptable.

## 7. Testing minimums

- Adapter unit tests (fixture/mocked platform payloads), search service tests, API tests (`/search`, `/health`, `/reports`), frontend component tests where worthwhile, stale-stream tests, failure-injection tests (quota/timeout/malformed/empty with other adapter healthy).
- Manual checklists live in roadmap sprints (e.g. 5 unrelated queries: titles/thumbnails/links match source, platform identified, no raw API leak).

## 8. Git / PR hygiene

- Do NOT work directly on `main` for sprint work. `main` stays green/deployable.
- Branch: `feat/<sprint>-<slug>` (e.g. `feat/0-1-repo-bootstrap`). Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Per-sprint flow: branch â†’ implement â†’ verify â†’ commit â†’ update `worklog.md` (can amend into sprint commit or separate `docs: worklog` â€” be consistent) â†’ push branch â†’ merge to `main` (PR if remote exists, else local `git merge --no-ff`) â†’ push `main`.
- PRs: link sprint (e.g. `Sprint 0.1`), describe verification performed, no secrets, update `docs/` if architecture/contract changed.
- Remote (once created): `github.com/<user>/streamsearch`. Create via `gh repo create streamsearch --private|--public --source=. --push` only after confirming visibility. Never force-push `main`.
- Definition of MVP done: user can open site â†’ search topic/event â†’ get normalized YouTube results â†’ see live/freshness + source/creator â†’ watch via embed or open source â†’ report bad results â†’ repeat searches without excessive API use.

## 9. For agents: do / do not

DO: read the 3 docs before coding; keep adapters replaceable; make freshness/reporting/caching explicit; ask if a task would violate ToS, add a platform early, or introduce embeddings/Redis/Postgres prematurely.
DO NOT: download/rehost video; call platform APIs from the browser in production design; use viewer count as primary rank; build giant synonym ontologies; add accounts/social/native-mobile unless justified in roadmap.
