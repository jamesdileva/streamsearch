# StreamSearch Worklog (append-only, newest at bottom)

Format per sprint: date, sprint, branch, what changed, verification + result, commit hash.

---

## 2026-10-02 — Bootstrap (pre-0.1)

- Sprint: repo bootstrap (docs move + AGENTS.md + README + .gitignore + .env.example)
- Branch: `main` (initial commit, exception to feature-branch rule — no code yet)
- What: reviewed `architecture.md`, `implementation-guide.md`, `sprint-roadmap.md`; created `AGENTS.md` with stack/conventions/sprint loop; moved docs to `docs/`; added `README.md`, `.gitignore`, `.env.example`; `git init -b main`
- Verification: `git status` clean; `gh auth status` OK (jamesdileva); no secrets committed; no remote yet
- Commit: `08bec98 chore: repo bootstrap with docs, AGENTS.md, README, gitignore`

## 2026-10-02 — Sprint workflow agreement

- Sprint: process only (no code)
- Branch: `main`
- What: encoded sprint loop `plan → scope → implement → verify → commit → worklog → push` in `AGENTS.md §3b`; clarified feature-branch model (`feat/<sprint>-<slug>`, merge to `main`); created this `worklog.md`
- Verification: n/a (docs only)
- Commit: `bd5a50e docs: sprint loop workflow + worklog (plan-scope-implement-verify-commit-worklog-push)`

## 2026-10-02 — Remote created + push

- Sprint: process only (no code)
- Branch: `main`
- What: created public GitHub repo `jamesdileva/streamsearch` via `gh repo create streamsearch --public --source=. --push`; `main` now tracks `origin/main`
- Verification: `git remote -v` shows origin; `git status -sb` clean, `main...origin/main`
- Commit: `923609d docs: worklog commit hash` (+ `6d02c18 docs: log remote creation + push`)

## 2026-10-03 — Sprint 0.1 Repository Bootstrap

- Sprint: 0.1 (Goal: clean foundation with working frontend/backend connection)
- Branch: `feat/0-1-repo-bootstrap`
- What: Vite React-TS shell (`App` fetches `GET /api/health` via `src/services/api.ts`, loading/ok/error states); FastAPI `app/main.py` (`/api/health`), env-only `app/config.py`, `adapters/base.py` (`BasePlatformAdapter` + `FakeAdapter`); toolchain locked (backend `ruff`, frontend `oxlint` + `vitest` + `tsc`); README quickstart + checks; removed Vite demo leftovers; `VITE_API_URL` via `frontend/.env.example`
- Non-goals (deferred): search UI (1.1), real YouTube adapter (1.2), DB/index/cache, Postgres/Redis, embeddings
- Verification:
  - Backend: `python -m pytest -q` → 1 passed; `python -m ruff check .` → clean; live `GET /api/health` → `{"status":"ok","env":"development"}`
  - Frontend: `npm run typecheck` OK; `npm run lint` (oxlint) OK; `npm run test` (vitest) → 2 passed; `npm run build` OK; dev server `http://localhost:5173/` → HTTP 200
  - Secrets: staged leak check empty (no `node_modules`/`dist`/`.env`/`__pycache__` tracked); no `.env` committed
- Commit: `bac97c8 feat: sprint 0.1 frontend shell + health wiring` (+ `af20f64 docs: worklog sprint 0.1`, merge `fe73443`)

## 2026-10-03 — Sprint 0.2 Architecture Skeleton

- Sprint: 0.2 (Goal: core boundaries real before feature work)
- Branch: `feat/0-2-architecture-skeleton`
- What: `app/api` router (`/api/health` moved, `/api/search?q=` skeleton); `models/stream.py` (`Stream` + `SearchResponse`); `services/search.py` placeholder (adapter fan-out, no scoring); `api/errors.py` envelope `{"error": {"code", "message"}}` (422 empty-query, 500 fallback; framework 404 keeps Starlette default); `FakeAdapter` returns one normalized fixture; frontend service layer `searchStreams()` + skeleton preview render; test-setup cleanup fix; README/AGENTS state
- Non-goals (deferred): search UI (1.1), YouTube (1.2), relevance/freshness/cache/persistence, custom 404 page
- Verification:
  - Backend: `python -m pytest -q` → 5 passed; `python -m ruff check .` → clean (fixed UP045 `X | None`, B008 `noqa` on FastAPI `Depends` idiom); live `GET /api/search?q=wildfire` → normalized fake stream `count: 1`; empty `q` → 422 envelope
  - Frontend: `npm run typecheck` OK; `npm run lint` OK; `npm run test` → 4 passed; `npm run build` OK; dev server → HTTP 200
  - Secrets: staged leak check empty; no `.env` tracked
- Commit: `4e23cd8 feat: sprint 0.2 architecture skeleton (...)` (+ `a9938d0 docs: worklog sprint 0.2`, merge `9e50b64`)

## 2026-10-03 — Sprint 1.1 Search Interface

- Sprint: 1.1 (Goal: primary search interaction with all states)
- Branch: `feat/1-1-search-interface`
- What: `components/SearchBar.tsx` (controlled input + submit, disabled while loading); `components/ResultsList.tsx` (minimal rows — card polish is 2.1); `App` flow idle/empty-query/loading/ok/error (`aria-live` results region); submit-only search (no per-keystroke fan-out); responsive CSS (fluid layout + 480px stacking); removed 0.2 hardcoded skeleton preview (superseded by real flow)
- Non-goals (deferred): card polish (2.1), real YouTube results (1.2/1.3), filters (8.1), query caps/rate limits (10.2)
- Verification:
  - Frontend: `npm run typecheck` OK; `npm run lint` (oxlint) OK; `npm run test` → 13 passed (empty/normal/long/special/repeated/empty-results/error + health); `npm run build` OK; dev server → HTTP 200; 480px stacking rule ships in `index.css` (narrow-viewport visual check left as manual)
  - Backend (untouched): `python -m pytest -q` → 5 passed regression; live `GET /api/search?q=concert` → fake fixture `count: 1`
  - Fixes during verify: test-setup `cleanup()` (accumulating renders), `findByText` → testid assertions (split text nodes)
  - Secrets: staged leak check empty; no `.env` tracked
- Commit: `c728c9a feat: sprint 1.1 search interface (...)` (+ `e60302a docs: worklog sprint 1.1`, merge `bc28794`)

## 2026-10-04 — Sprint 1.2 YouTube Adapter (live verify deferred)

- Sprint: 1.2 (Goal: first real platform; no key available so live verification deferred)
- Branch: `feat/1-2-youtube-adapter`
- What: `adapters/youtube.py` (Data API v3 `search.list` eventType=live + `videos.list` snippet/liveStreamingDetails/recordingDetails → normalized `Stream`; only verifiably-live kept; budget-clamped `max_results`, 10s timeout); `AdapterError`/`AdapterConfigError` (no secrets in messages); key-driven factory (`YouTubeAdapter` iff `YOUTUBE_API_KEY`, else `FakeAdapter`); `YOUTUBE_MAX_RESULTS` config; no frontend changes (normalized-only boundary holds)
- Non-goals (deferred): live-query verification until key exists; failure-isolation status reporting (10.1); relevance (3.1); caching (4.1)
- Verification:
  - Backend: `python -m pytest -q` → 16 passed (11 new, all `httpx.MockTransport`, zero network); `python -m ruff check .` → clean
  - Covered: full mapping incl. location/viewers/tags, non-live filtering, empty candidates skip videos call, missing key → `AdapterConfigError`, 500/403/malformed → `AdapterError`, budget clamp, factory both ways, service validates records
  - Live: no-key smoke `GET /api/search?q=storm` → fake fixture unchanged; frontend untouched (checks skipped)
  - Correction during verify: key in query string is by YouTube API design (HTTPS) — test asserts key absence from error messages instead
  - Secrets: staged leak check empty; no `.env`/key tracked
- Deferred smoke procedure (run once `YOUTUBE_API_KEY` exists): set key in `backend/.env`, restart uvicorn, `GET /api/search?q=` for news/wildfire/storm/gaming/concert → expect `platform: youtube` records each with `actualStartTime`-backed `started_at`; open `source_url`s to confirm actually live
- Commit: `18b38e6 feat: sprint 1.2 youtube adapter (key-gated, mocked tests)` (+ `026c44e docs: worklog sprint 1.2`, merge `b095afd`)

## 2026-10-04 — Sprint 1.3 Real Search Results (source-truth half deferred)

- Sprint: 1.3 (Goal: full chain end-to-end; still no key, so source-truth checks deferred)
- Branch: `feat/1-3-real-search-results`
- What: `AdapterError` → 502 envelope in search route (no internals leak; per-platform status stays in 10.1); parametrized 5-query sweep test; response-keys ⊆ `Stream` fields test (API + YouTube raw records); result-count line in UI ("Found N live streams")
- Non-goals (deferred): title/thumbnail/link-vs-source matching until key; card polish (2.1); per-platform status/partial results (10.1)
- Verification:
  - Backend: `python -m pytest -q` → 24 passed; `python -m ruff check .` → clean (fixed own duplicated route def, F811)
  - Frontend: `npm run typecheck` OK; `npm run lint` OK; `npm run test` → 13 passed; `npm run build` OK; dev server → HTTP 200
  - Live: no-key smoke `GET /api/search?q=gaming` → fake fixture; chain SearchBar→rows intact
  - Secrets: staged leak check empty; no `.env`/key tracked
- Deferred (once key exists): 5-query source-truth pass per README procedure — results appear, titles/thumbnails match source, links open live broadcasts, platform identified, no raw API fields in UI
- Commit: `c963b61 feat: sprint 1.3 real search chain (...)` (+ `1e2f385 docs: worklog sprint 1.3`, merge `1d96658`)

## 2026-10-04 — Sprint 2.1 Stream Cards

- Sprint: 2.1 (Goal: results useful without opening first; still no key, so source comparison deferred)
- Branch: `feat/2-1-stream-cards`
- What: `StreamCard` (live badge, title, channel, platform, 16:9 thumbnail w/ empty placeholder, start `<time>`, viewers/location rows, Watch/Open-Source buttons; every optional field omitted when unavailable) + `LiveStatus` + `PlatformBadge`; `ResultsList` renders cards; full `Stream` type mirror; responsive auto-fill grid (1 col ≤480px)
- Non-goals (deferred): card-vs-source comparison until key; freshness states (2.2); reporting (2.3)
- Verification:
  - Frontend: `npm run typecheck` OK; `npm run lint` (oxlint) clean; `npm run test` → 16 passed (full/minimal/ended card matrix + updated flow tests); `npm run build` OK; dev server → HTTP 200
  - Backend (untouched): `python -m pytest -q` → 24 passed regression
  - Fixes during verify: `data-testid` on decorative thumb (empty `alt` hides role), `PlatformBadge` prop typed via `Stream['platform']` (unused import)
  - Secrets: staged leak check empty; no `.env`/key tracked
- Deferred (once key exists): card-vs-source pass per README — title/thumbnail/channel match source page, buttons open live broadcast + source, platform badge correct
- Commit: `30b9d97 feat: sprint 2.1 stream cards (...)` (+ this worklog entry pending)
