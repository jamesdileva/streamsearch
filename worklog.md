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
- Commit: `30b9d97 feat: sprint 2.1 stream cards (...)` (+ `3c54d85 docs: worklog sprint 2.1`, merge `2e8bffd`)

## 2026-10-04 — Sprint 2.2 Live Freshness

- Sprint: 2.2 (Goal: stale information must not look current)
- Branch: `feat/2-2-live-freshness`
- What: `services/freshness.py` (`fresh` ≤300s / `aging` ≤1800s / `stale` / `ended`, env thresholds `FRESHNESS_*_SECONDS`, skew-clamped, adapters never set it); service stamps `Stream.freshness` on every search; `LiveStatus` shows trust note (`Fresh`, `Aging · verified 12m ago`, `Stale · not verified`; none when ended); `lib/time.ts` relative age
- Non-goals (deferred): persistent index (4.2) and periodic revalidation (4.3) — request-time discovery re-verifies each search, so live results are fresh by construction until stored records exist; reporting (2.3)
- Verification:
  - Backend: `python -m pytest -q` → 35 passed (11 new simulations: fresh/boundaries/aging/stale/never-verified/ended/future-skew/custom thresholds/config defaults/service stamping); `python -m ruff check .` → clean (applied PLR1730 `max()`)
  - Frontend: `npm run typecheck` OK; `npm run lint` clean; `npm run test` → 19 passed (time buckets, aging verified-age, ended suppresses note); `npm run build` OK; dev server → HTTP 200
  - Live: `GET /api/search?q=storm` → `"freshness":"fresh"` stamped
  - Secrets: staged leak check empty; no `.env`/key tracked
- Commit: `5f63222 feat: sprint 2.2 live freshness (...)` (+ `6e5131b docs: worklog sprint 2.2`, merge `f4e638f`)

## 2026-10-04 — Sprint 2.3 Broken/Stale Reporting

- Sprint: 2.3 (Goal: users feed corrections back into the system)
- Branch: `feat/2-3-reporting`
- What: `ReportButton` per card (4 radio reasons + optional ≤500-char detail + sent/error states); `POST /api/reports` → 201 SQLite-persisted `Report`; `GET /api/reports` list + `stream_id` filter; keyed on `platform_stream_id`; only light validation today (full abuse controls wait for 11.2)
- Non-goals (deferred): moderation UI/takedown handling (11.1); report-driven revalidation (uses index from 4.2+); rate limiting (10.2)
- Verification:
  - Backend: `python -m pytest -q` → 44 passed (9 new: all 4 reasons persist + list/filter/detail round-trip/422s); `python -m ruff check .` → clean (fixed whitespace-only `stream_id` via `StringConstraints`)
  - Frontend: `npm run typecheck` OK; `npm run lint` clean; `npm run test` → 27 passed (8 new: 4 reasons, details, error, cancel); `npm run build` OK; dev server → HTTP 200
  - Live: `POST /api/reports` → 201 + `GET /api/reports?stream_id=` round-trip; smoke `.db` removed after, `*.db` gitignored
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/key tracked
- Commit: `07bf8e5 feat: sprint 2.3 stale reporting (...)` (+ `54f4cc7 docs: worklog sprint 2.3`, merge `b1bebbe`)

## 2026-10-04 — Sprint 3.1 Deterministic Relevance

- Sprint: 3.1 (Goal: stop treating every API result as equally useful)
- Branch: `feat/3-1-deterministic-relevance`
- What: `app/search/scoring.py` (`Weights` frozen dataclass + defaults, `score_stream` breakdown, `rank_streams`; title exact 100 / token 40, location 50, description/tags 15, freshness 20, viewers 5 log-scaled; ended partition last, stable ties); service ranks + stamps `Stream.score`; UI order-only (no score display); tokenizer lives in scoring (3.2 builds on it)
- Non-goals (deferred): query normalization/synonyms (3.2); location parsing (3.3); semantic retrieval (waits for 7.1 dataset)
- Verification:
  - Backend: `python -m pytest -q` → 55 passed (11 new labeled-set: exact>token>irrelevant, desc/tag/location lifts, freshness tiebreak, ended demotion, viewers tiebreak-only + never-beats-title, custom weights, stable ties, empty query, cross-adapter service ranking); `python -m ruff check .` → clean
  - Frontend (type touch-up only): `npm run typecheck` OK; `npm run lint` clean; `npm run test` → 27 passed; `npm run build` OK; dev server → HTTP 200
  - Corrections during verify: multi-token labeled query (single-token makes token-fractions binary); fixed own duplicated imports in `search.py`
  - Live: `GET /api/search?q=wildfire` → `"score":160.0` stamped
  - Secrets: staged leak check empty; no `.env`/key tracked
- Commit: `5beee37 feat: sprint 3.1 deterministic relevance (...)` (+ `1e43bfb docs: worklog sprint 3.1`, merge `213e9e0`)

## 2026-10-04 — Sprint 3.2 Search Normalization

- Sprint: 3.2 (Goal: small query variations produce sensible results, no AI)
- Branch: `feat/3-2-search-normalization`
- What: `app/search/normalize.py` (`phrase_tokens` order-preserving + `tokens` set + `normalized_text`; 13-entry `SYNONYMS`: la/nyc + 11 event plurals; ≤20 pinned); scoring uses it symmetrically (queries + fields), exact = contiguous expanded-phrase run; no stemming rules, non-ASCII dropped (multilingual = Phase 15)
- Non-goals (deferred): location-meaning parsing (3.3); semantic retrieval (7.1)
- Verification:
  - Backend: `python -m pytest -q` → 63 passed (8 new pair-equivalence: case/punct/space, plurals, LA expansion, canonical form, empty, map-size guard, identical ranking, no-stemming-misfire); `python -m ruff check .` → clean
  - Frontend untouched (no type changes): checks skipped
  - Correction during verify: plural test exposed raw-phrase exact gap → fixed with contiguous expanded-phrase matching (all 3.1 tests still pass)
  - Live: `?q=WILDFIRES` vs `?q=wildfire` → identical `score: 160.0` (raw `query` echo + fake-fixture title/timestamps differ by design — echo contract + per-request fixture)
  - Secrets: staged leak check empty; no `.env`/key tracked
- Commit: `a1421e5 feat: sprint 3.2 query normalization (...)` (+ `9b4bac3 docs: worklog sprint 3.2`, merge `f69e28a`)

## 2026-10-05 — Sprint 3.3 Location-Aware Search

- Sprint: 3.3 (Goal: location becomes a useful search dimension, not decoration)
- Branch: `feat/3-3-location-search`
- What: `app/search/location.py` (near/in/suffix parsing on synonym-expanded text; 12-place gazetteer with coords, ≤20 pinned; unknown places stay keyword with `place_attempt` exposed); place-directed scoring (coverage of requested place; legacy query-overlap when no place); service splits topic/place for ranking while adapters get the full query; YouTube `location`/`locationRadius` geo bias when keyed (`YOUTUBE_LOCATION_RADIUS`, default 100km)
- Non-goals (deferred): hierarchical geo (city-in-state matching); map UI (8.2 experiment); semantic retrieval (7.1)
- Verification:
  - Backend: `python -m pytest -q` → 75 passed (12 new matrix: near/in/suffix, case/punct/synonyms, unknown, none, bare-place, gazetteer guard+coords, place outranking, no-match stability, service end-to-end, YouTube geo present/absent); `python -m ruff check .` → clean
  - Frontend untouched (no type changes): checks skipped
  - Live: `?q=wildfire near Los Angeles` + `?q=storm near nowhereville` → 200, ranked, scored (fake has no `location_text`, differentiation proven in tests)
  - Secrets: staged leak check empty; no `.env`/key tracked
- Commit: `a21541b feat: sprint 3.3 location-aware search (...)` (+ `285de4e docs: worklog sprint 3.3`, merge `0de2192`)

## 2026-10-05 — Sprint 4.1 Search Result Caching

- Sprint: 4.1 (Goal: repeated searches are cheap and fast; protect quotas)
- Branch: `feat/4-1-result-caching`
- What: `services/cache.py` (in-memory TTL cache keyed by normalized query + adapter set, expired purged on access, successes only) + `CacheStats` (hits/misses/adapter calls/errors); service serves repeats from cache; `GET /api/stats` exposes counters (seed for 10.3); `CACHE_TTL_SECONDS` (default 60)
- Non-goals (deferred): persistent index (4.2); background refresh (4.3); Redis (needs traffic justification); failure caching (errors stay visible/retryable)
- Verification:
  - Backend: `python -m pytest -q` → 83 passed (8 new: repeat=1 call, raw-variant sharing, distinct queries, zero-TTL, failures uncached + error counts, key mixing, purge-on-write, stats shape); `python -m ruff check .` → clean (fixed import sort)
  - Frontend untouched (no type/contract changes): checks skipped
  - Design call during verify: synonyms stay separate cache keys (platforms match on raw wording) — case/punct/space variants share
  - Live: 2× `?q=storm` → `{"cache_hits":1,"cache_misses":1,"adapter_calls":1,"adapter_errors":0,"cache_size":1}` — platform queried once
  - Secrets: staged leak check empty; no `.env`/key tracked
- Commit: `9356a4d feat: sprint 4.1 short-lived result cache (...)` (+ `5e4fa57 docs: worklog sprint 4.1`, merge `f191124`)

## 2026-10-05 — Sprint 4.2 Persistent Stream Index

- Sprint: 4.2 (Goal: from request-time discovery toward a real searchable index)
- Branch: `feat/4-2-stream-index`
- What: `services/index.py` (SQLite `streams`, PK `(platform, platform_stream_id)`; upsert refreshes `last_seen_at` + overwrites metadata, preserves `first_seen_at`, sets `ended_at` on live→ended, clears on re-live; `IndexedStream` adds first/last-seen + ended; `prune_ended_older_than` ended-only; shared `services/db.py` with reports refactored onto it); service upserts on cache misses (never breaks search — logged + skipped); `index_records`/`index_live` in `/api/stats`
- Non-goals (deferred): background refresh (4.3); pruning unseen actives (needs refresh first); search-from-index (still adapter-first); Postgres (unjustified)
- Verification:
  - Backend: `python -m pytest -q` → 90 passed (7 new: no-dupes + first/last-seen, overwrite, ended + stable transition time, re-live clears, typed round-trip, ended-only prune, service populate without dupes); `python -m ruff check .` → clean
  - Frontend untouched (no contract changes): checks skipped
  - Live: from empty DB, 1× `?q=storm` → `index_records:1, index_live:1`; smoke `.db` removed after (`*.db` ignored)
  - Note: non-isolated tests share the CWD dev DB file (gitignored); isolated suites use tmp DBs — revisit with dependency_overrides if it bites
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/key tracked
- Commit: `dff87b9 feat: sprint 4.2 persistent stream index (...)` (+ `0a51d19 docs: worklog sprint 4.2`, merge `f7b341b`)

## 2026-10-05 — Sprint 4.3 Background Refresh

- Sprint: 4.3 (Goal: continuous freshness without waiting for searches)
- Branch: `feat/4-3-background-refresh`
- What: `reverify` contract on adapters (dict=live, None=ended/gone, absent=untouched; default unsupported); `services/refresh.py` bounded pass (stalest live first, per-platform grouping, ended transitions, ended-prune, per-adapter errors recorded); `POST /api/refresh` trigger + lifespan interval loop (`REFRESH_*`, on/modest: 900s, batch 10, prune 30d); YouTube batch id-lookup (50/call); Fake stays live; query-discovery explicitly excluded (no crawler)
- Non-goals (deferred): discovery of popular queries (unjustified without traffic); persistent refresh counters (10.3); trigger auth (10.2/11.2 — do not expose publicly)
- Verification:
  - Backend: `python -m pytest -q` → 98 passed (8 new: last_seen advance, gone→ended, unsupported untouched, error isolation, batch limit, prune-in-pass, trigger shape, YouTube live/gone mapping); `python -m ruff check .` → clean
  - Frontend untouched (no contract changes): checks skipped
  - Corrections during verify: Fake fixture id kept stable (`fake-1`) across search/reverify refactor
  - Live: from empty DB, search → `POST /api/refresh` → `{checked:1, refreshed:1, ended:0, pruned:0, errors:[]}`; stats consistent; smoke `.db` removed after (transient lock from kill timing — retried clean)
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/key tracked
- Commit: `cab6594 feat: sprint 4.3 background refresh (...)` (+ `d0c13d1 docs: worklog sprint 4.3`, merge `b6201d8`)

## 2026-10-07 — Sprint 5.1 Adapter Contract Review

- Sprint: 5.1 (Goal: prove the architecture supports a second platform)
- Branch: `feat/5-1-adapter-contract-review`
- What: `adapters/fake_twitch.py` (`FakeTwitchAdapter`: numeric ids, game-name categories, zero location, missing thumb + no-embed record, int-or-absent viewers, live/nothing states; retired `555` for refresh-ending); no-key defaults now `[FakeAdapter, FakeTwitchAdapter]` (never mixed with real); zero interface changes
- Assumption review (grep): `app/search` has no platform refs; `app/api` + `app/models` none; `services` only the key-driven factory; frontend only opaque platform strings in fixtures (badge renders whatever arrives) — no platform parsing in UI
- Non-goals (deferred): real Twitch adapter (5.2); unifying fake adapters (kept separate: skeleton vs Twitch-shaped)
- Verification:
  - Backend: `python -m pytest -q` → 103 passed (5 new: differing-shape validation, mixed ranking, reverify judgements, mixed refresh endings, factory never mixes fake+real); `python -m ruff check .` → clean
  - Updated 2 tests for the new default reality (mixed search shape, `[fake, twitch]` factory); all other suites unaffected
  - Frontend untouched (mocks; twitch records carry all card fields): checks skipped
  - Live: `?q=concert` → 3 records, `twitch > fake > twitch` by score (viewer bonus + stable ties), platforms identified; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/key tracked
- Commit: `585a88d feat: sprint 5.1 second fake platform (...)` (+ this worklog entry pending)
