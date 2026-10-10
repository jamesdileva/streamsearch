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
- Commit: `585a88d feat: sprint 5.1 second fake platform (...)` (+ `ac16fc4 docs: worklog sprint 5.1`, merge `a7f43fe`)

## 2026-10-07 — Sprint 5.2 Twitch Discovery (live verify deferred)

- Sprint: 5.2 (Goal: second real platform; no credentials, so live verification deferred)
- Branch: `feat/5-2-twitch-discovery`
- What: `adapters/twitch.py` (Helix `search/categories` → `streams` + top-live fallback; channel-stable `platform_stream_id` with broadcast id in metadata; game-name categories; substituted thumbnails; client-credentials token cache + single 401 retry; channel reverify ≤100/call; `TWITCH_MAX_RESULTS/CATEGORIES/EMBED_PARENT` config); factory matrix yt/twitch/both/fakes-never-mixed
- Non-goals (deferred): dual-platform live proof until both credentials exist; unified ranking balance review (5.3); category pagination (first page only, bounded)
- Verification:
  - Backend: `python -m pytest -q` → 113 passed (10 new: mapping, category cap, fallback, token caching, 401 retry, reverify live/offline, config errors, 500, factory matrix, service validation); `python -m ruff check .` → clean
  - Frontend untouched (real twitch records carry all card fields; no type changes): checks skipped; dev server → HTTP 200
  - Live: no-cred smoke shape unchanged (fake + fake-twitch, 3 ranked); smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Deferred dual-platform procedure (needs both keys): set `YOUTUBE_API_KEY` + `TWITCH_CLIENT_ID/SECRET` in `backend/.env` (+ `TWITCH_EMBED_PARENT` for production host), restart, `GET /api/search?q=` for news/gaming/concert → expect `youtube` + `twitch` records in one ranked set, each verifiably live via `source_url`; confirm neither platform dominates every query
- Commit: `3a95837 feat: sprint 5.2 twitch discovery (...)` (+ `4017aaa docs: worklog sprint 5.2`, merge `5ca389b`)

## 2026-10-08 — Sprint 5.3 Unified Cross-Platform Results

- Sprint: 5.3 (Goal: stop thinking in platform columns)
- Branch: `feat/5-3-unified-results`
- What: server-side `platform` / `sort=relevance|newest|viewers` / `has_location` params (unknown sort → 422; unknown platform → empty, not error; ended-last partition kept across sorts; nulls sort last); `sort_streams` in scoring; filter-aware cache keys; `SearchFilters` UI (platform options derived from results, never hardcoded; auto-refetch on change, none before first search) + `lib/filters.ts`
- Non-goals (deferred): dual-platform live proof until both credentials exist; richer 8.1 filters (language etc.); per-platform status (10.1)
- Verification:
  - Backend: `python -m pytest -q` → 121 passed (8 new: no-domination tie, platform filter incl. case/unknown, newest/viewers ordering + nulls/ended placement, location filter, key separation, API params, unknown-sort 422); `python -m ruff check .` → clean
  - Frontend: `npm run typecheck` OK; `npm run lint` clean (moved filter types to `lib/filters.ts` after Fast Refresh warning); `npm run test` → 33 passed (3 SearchFilters + 3 App filter tests + updated call assertions); `npm run build` OK; dev server → HTTP 200
  - Live: mixed `?q=storm` → 3 records fake+twitch; `&platform=twitch` → 2 twitch-only; `&sort=viewers` → `[5231, None, None]`; bad sort → 422 envelope; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: `5106f4d feat: sprint 5.3 unified cross-platform results (...)` (+ `c05dbe4 docs: worklog sprint 5.3`, merge `42d3934`)

## 2026-10-08 — Sprint 6.1 Event vs. Stream Data Model

- Sprint: 6.1 (Goal: one event → many broadcasts, as a persisted concept)
- Branch: `feat/6-1-event-model`
- What: `models/event.py` (`Event`: auto `evt_*` id, non-empty topic, optional location, detected_at, active_until, `related_streams[]` as `(platform, platform_stream_id)` refs, `is_active()`); `services/events.py` (SQLite `events` + `event_streams`; create/get/add-idempotent/close/list-active; refs not FK-enforced by design; duplicate ids → ValueError)
- Non-goals (deferred): automatic clustering (6.2/6.3); event API endpoints (when UI/clustering needs them); report-driven grouping
- Verification:
  - Backend: `python -m pytest -q` → 131 passed (10 new: cross-platform manual group, auto-id/defaults, blank-topic + duplicate-id rejection, idempotent add, unknown-event errors, close + active filter + re-close no-op, get-unknown None, active boundary); `python -m ruff check .` → clean (fixed import order, blind-except)
  - Frontend untouched (no contract changes): checks skipped
  - Corrections during verify: insertion-ordered refs (not platform-sorted); public `new_event_id()` (throwaway `Event()` fails required-topic validation)
  - Live: app boots, health ok, mixed search shape unchanged; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: `41a8a9d feat: sprint 6.1 event vs stream data model (...)` (+ `2b082ba docs: worklog sprint 6.1`, merge `fb3a808`)

## 2026-10-08 — Sprint 6.2 Basic Duplicate Detection

- Sprint: 6.2 (Goal: collapse obvious duplicates, never unrelated streams)
- Branch: `feat/6-2-duplicate-detection`
- What: `app/search/dedup.py` (same-id always; same-channel + title Jaccard ≥0.8 + 6h start window; missing times can't disprove; different channels never collapse incl. cross-platform); best-ranked survives (post-rank collapse); `duplicates_removed` on `SearchResponse`; index keeps every sighting
- Non-goals (deferred): event clustering/grouping (6.3 — dedup must not do its job); UI display of removed count; per-creator cross-event logic
- Verification:
  - Backend: `python -m pytest -q` → 139 passed (8 new manual set: same-id, same-channel overlap, cross-platform simulcast, different-topics survive, different-channels-same-title survive, far-apart-time survives, missing-times collapse, service collapse + index-keeps-sightings); `python -m ruff check .` → clean
  - All pre-existing suites unaffected (fixtures correctly never collapse); frontend untouched (additive response field only): checks skipped
  - Live: `?q=storm` → count 3, removed 0 (no false collapse in production path); smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: `08b0cb7 feat: sprint 6.2 basic duplicate detection (...)` (+ `55459c7 docs: worklog sprint 6.2`, merge `fadd242`)

## 2026-10-08 — Sprint 6.3 Event Clustering Experiment

- Sprint: 6.3 (Goal: test whether streams can be grouped around an ongoing event)
- Branch: `feat/6-3-clustering-experiment`
- What: `app/search/clustering.py` (EXPERIMENTAL, unwired): union-find over `title_link AND (location_link OR time_link) AND NOT time_veto`; stopword-filtered title Jaccard (doubles as shared-entity signal); topic_guess + location notes per cluster; no semantic similarity (stays behind the 7.1 gate)
- Non-goals (deferred): production wiring (explicitly not done); semantic embeddings; event endpoints/UI
- Verification (fixture set: wildfire trio, concert pair, 3 same-city distractors, edge pairs):
  - Backend: `python -m pytest -q` → 147 passed (8 new); `python -m ruff check .` → clean (fixed SIM905 list literal)
  - Measured at 0.4: concert pair ✓ + wildfire pair ✓, zero cross-story merges — BUT same-city traffic distractor joins the wildfire cluster (my hand analysis wrongly predicted exclusion; city-word overlap clears 0.4 on short titles)
  - Measured at 0.6: FP gone — along with both true groups (total fragmentation)
  - Statewide roundup stays separate at both points (ambiguous by design: region-vs-city wording + fire/wildfire lexical gap)
  - Same-title pair clusters; 3-day-apart rebroadcasts split via veto; stopwords pinned ≤30
  - Frontend untouched: checks skipped; live boot + search shape unchanged; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Verdict: KEEP OUT of production. No threshold separates city-word overlap from topic-word overlap on short titles — that needs lexical/semantic equivalence (fire≈wildfire), i.e. real-data + semantic work in 7.x. Deterministic grouping is fine for obvious cases but untrustworthy exactly where it matters (concurrent same-city events). Revisit with real data; do not tune further on fixtures.
- Commit: `ffa63bd feat: sprint 6.3 event clustering experiment (...)` (+ `35078cf docs: worklog sprint 6.3 with verdict`, merge `c9941f5`)

## 2026-10-08 — Sprint 7.1 Failure Dataset

- Sprint: 7.1 (Goal: determine whether keyword search is actually insufficient)
- Branch: `feat/7-1-failure-dataset`
- What: `backend/benchmarks/failure_dataset.py` (8 hand-labeled cases + `evaluate` mirroring the service + `summarize`/`report`; runnable via `python -m benchmarks.failure_dataset`); `tests/test_failure_dataset.py` tripwires (controls must pass, gaps must fail exactly as recorded, classes known, counts pinned)
- Non-goals (deferred): embedding prototype (7.2); production semantics (never on this evidence alone); real-traffic failure mining (needs traffic)
- Verification:
  - Benchmark output: 5 FAIL as documented (vocabulary-gap, synonym-gap, description-weight, vague-title, phrase-vs-meaning) + 3 controls PASS → `passed=3 failed=5`
  - Backend: `python -m pytest -q` → 151 passed (4 new tripwires); `python -m ruff check .` → clean (fixed cp1252 console crash: ASCII-only report)
  - Frontend untouched (evaluation tooling only): checks skipped; live boot + search shape unchanged; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Verdict: YES, keyword search is insufficient ON ADVERSARIAL CASES — which justifies a 7.2 prototype measured against this same set (must fix gaps without regressing controls), not a production decision. Representative-traffic measurement still owed once real queries exist.
- Commit: `498669d feat: sprint 7.1 keyword failure dataset (...)` (+ `0e1891d docs: worklog sprint 7.1 with verdict`, merge `e77f733`)

## 2026-10-08 — Sprint 7.2 Embedding Search Prototype (unwired)

- Sprint: 7.2 (Goal: compare keyword vs semantic vs hybrid on the 7.1 set)
- Branch: `feat/7-2-embedding-prototype`
- What: `app/search/embeddings.py` (Ollama `/api/embed` client — HTTP only, NO torch/transformers dependency — with text cache; `record_text` = title+description+channel; `cosine` clamped; `hybrid_rank` min-max normalizes keyword+semsim and blends at keyword_weight=0.5); `benchmarks/embedding_experiment.py` (runner replaying the 7.1 set three ways, `python -m benchmarks.embedding_experiment`); `OLLAMA_HOST`/`EMBEDDINGS_MODEL` config. Production search untouched — this module is never called by it.
- Model chosen: `nomic-embed-text` (137M, 768-dim, 274MB) — smallest true embedding model already installed (`phi4-mini`/`qwen3.5:4b` are chat models without reliable embed endpoints).
- Verification:
  - Experiment (run twice, reproducible): keyword=3/8 semantic=4/8 hybrid=4/8. Only `description-weight` flips; all 3 controls held (no regression); vocab-gap, synonym-gap, vague-title, phrase-vs-meaning all still fail.
  - Margin check: `record_text`-above-query sims are 0.63–0.69 vs keyword-literal matches at 0.71–0.84 — the model ranks *lexically-similar* records above *semantically-relevant* ones, which is the worst possible inversion for hybrid blending.
  - Backend: `python -m pytest -q` → 163 passed (12 new: cosine/clamp/record_text, fake-vector hybrid blends + flat-normalization + weight control, mocked client error paths, plus Ollama-guarded integration tests incl. a tripwire that semantic top is the wrong record); `python -m ruff check .` → clean
  - Frontend untouched (no contract changes): checks skipped; dev server HTTP 200; live search shape unchanged; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Verdict: NOT ADOPTED for production. Negative result is well-supported: (a) +1/8 with zero movement on the gap class that motivated the experiment; (b) semantic scoring actively inverts relevance vs lexically-similar records; (c) description semantics aren't even used by 3.1's keyword signal yet — fixing that is much cheaper.
- Cheapest next step when wanted (NOT now): swap one of your existing chat models' embed endpoints or pull a larger embedder (e.g. `mxbai-embed-large`) and re-run `python -m benchmarks.embedding_experiment` — same command, same data, no code change. Decide after that.
- Commit: (this worklog entry pending)

## 2026-10-08 — Sprint 7.2b Embedding Bake-off (4 models)

- Sprint: 7.2b (Goal: separate "semantic doesn't help" from "this model doesn't help")
- Branch: `feat/7-2b-embedding-bakeoff`
- Method fix (important): added `ModelPreset` per-model documented query/doc prefixes, wired through `embed_query`/`embed_documents` with prefix-keyed caching and `EMBEDDINGS_QUERY_PREFIX`/`EMBEDDINGS_DOC_PREFIX` overrides. Presets cite sources: nomic `search_query:`/`search_document:`, qwen3 `Instruct:{task}\nQuery:`, embeddinggemma `task: search result | query: `/`title: none | text: `, bge-m3 none. The original 7.2 run embedded raw text both sides — outside nomic's documented operating condition, so its negative result was confounded.
- Pulled (311GB free; 2.7GB total): `embeddinggemma` 622MB, `qwen3-embedding:0.6b` 639MB, `bge-m3` 1.2GB — pulled while the other project shared Ollama, no contention problems.
- Bake-off (`python -m benchmarks.embedding_experiment --verbose`), each model in its documented config:
  - `nomic-embed-text` (137M): kw 3/8, sem 4/8, hyb 4/8
  - `embeddinggemma` (308M): kw 3/8, sem 4/8, hyb 4/8
  - `qwen3-embedding:0.6b`: kw 3/8, sem 4/8, hyb 4/8
  - `bge-m3` (567M): kw 3/8, sem **5/8**, hyb **5/8** ← best by exactly one case
  - **All four fail the identical 3 cases** (vocab-gap, synonym-gap, vague-title). Model size/capability does not move the failure class — it is inherent to short-text bi-encoders on adversarial synonym pairs.
- Prefix re-baseline: nomic *with* documented prefixes scores the same 3/4/4 as without. The confound was real in theory, immaterial in practice on this set — recorded rather than spun.
- Root-cause finding (most valuable): the only case any model fixes (`description-weight`) is fixed by one keyword weight constant. `description` weight 15→25 puts the keyword baseline at 4/8 — matching the best embedding model, with zero dependencies, zero latency, and no external service. Root cause: descriptions are weighted 15 vs title tokens 40, so "topic in description, distractor in title" loses.
- Verification:
  - Backend: `python -m pytest -q` → 168 passed (5 new preset tests incl. prefix-on-the-wire and prefix-aware cache; overlap integration tripwire updated to assert the measured-inversion); `python -m ruff check .` → clean (fixed an IndexError on empty doc_prefix in the table)
  - Frontend untouched (benchmark tooling only): checks skipped; dev server HTTP 200
  - Live: bake-off ran clean end-to-end on 4 models; search shape unchanged; no `.db` written by benchmarks
  - Secrets: staged leak check empty; no `.env`/creds tracked
- Verdict: DO NOT wire embeddings into search. Evidence is now 4 models × 2 configurations rather than 1 model × 1 config: the gain is 1–2 cases, never on the gap class that motivated the work, and it is dominated by a free weight fix. Keep `embeddings.py` + the runner + presets (cheap to re-run: `EMBEDDINGS_MODEL=<m> python -m benchmarks.embedding_experiment`) but require a meaningfully larger failure dataset (real traffic) before revisiting. Next step for 7.3 is the weight change, not hybrid ranking.
- Commit: `61fcd2d feat: sprint 7.2b embedding bake-off (...)` (+ merge `1fec344`)

## 2026-10-08 — Sprint 7.3 Hybrid Ranking (decision: NOT adopted)

- Sprint: 7.3 (Goal: combine deterministic + semantic ranking *if justified*)
- Branch: `feat/7-3-hybrid-ranking-decision`
- Decision: hybrid ranking is **NOT** adopted. The 7.2b bake-off showed semantic retrieval adds 1–2 cases on an adversarial set and never closes the gap class that motivated it, so blending would add an external dependency (Ollama), latency, and failure modes for no measurable benefit. Deterministic ranking stays the only production ranker; `embeddings.py` stays experimental and unwired.
- What DID ship: `Weights.description` 15 → 25 in `app/search/scoring.py`, the one measured gain from the whole semantic line of work, with a comment citing the evidence. Root cause: a title token (40) outranked a topic living in a description (15).
- Reclassification (tripwire working as designed): the weight fix flipped the pinned `description-weight` case, failing `test_documented_gaps_fail_as_recorded` exactly as intended. Moved it from gaps to controls in `benchmarks/failure_dataset.py` with a note explaining it was fixed by a weight change, not semantics.
- Verification:
  - Benchmark: `python -m benchmarks.failure_dataset` → `passed=4 failed=4` (was 3/5). Controls now 4 (incl. reclassified `description-weight`), gaps still 4 (vocabulary-gap, synonym-gap, vague-title, phrase-vs-meaning) all still failing as recorded.
  - Backend: `python -m pytest -q` → 168 passed; `python -m ruff check .` → clean. Updated pinned counts (4 controls / 4 gaps / (4,4) summary) and removed `description-weight` from the known-failure-class set.
  - Frontend: `npm run typecheck` OK; `npm run lint` clean; `npm run test` → 33 passed; `npm run build` OK (no contract change — ranking behaviour only)
  - Live: `?q=storm` → 3 ranked results, `removed: 0`, distinct scores preserved across platforms; stats consistent; smoke `.db` removed after
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Deferred: revisit embeddings only with a meaningfully larger **real-traffic** failure dataset; root-cause fixes for the 4 remaining gaps (vocabulary/synonym) would need a lexical-level approach (e.g. small curated synonym map), which is a cheaper next candidate than embeddings.
- Commit: `82e3aa1 feat: sprint 7.3 hybrid ranking decision (...)` (+ merge `428a23d`)

## 2026-10-08 — Sprint 8.1 Search Filters

- Sprint: 8.1 (Goal: make large result sets manageable)
- Branch: `feat/8-1-search-filters`
- Scope note: platform / sort / has_location already shipped in 5.3, so this sprint adds only the two genuinely new dimensions — **language** and **min viewers**.
- What: `Stream.language` (YouTube `defaultAudioLanguage`/`defaultLanguage`, Twitch `language`; BCP-47 primary subtag, lowercase; absent stays absent — never guessed); language filter (exact, case-insensitive) and min-viewers floor (records with unknown viewer counts are excluded, not silently passed); filter-aware cache keys; language + platform options derived from live results in the UI, never hardcoded; min-viewers number input with blank→0.
- Non-goals (deferred): map experiment (8.2); multilingual search itself (Phase 15 — this only *filters* on reported language); geo-radius drill-down.
- Verification:
  - Backend: `python -m pytest -q` → **180 passed** (13 new in `tests/test_filters.py`: language helper subtag/absent, YouTube + Twitch population via mocked transports, exact/case-insensitive matching, unknown-language exclusion, min-viewers floor semantics incl. unknown exclusion + combining, API params, negative→422, cache-key separation); `python -m ruff check .` → clean
  - Frontend: `npm run typecheck` OK; `npm run lint` clean; `npm run test` → **38 passed** (5 SearchFilters + 2 App tests: language options exclude null, min-viewers refetch); `npm run build` OK
  - Consistency fix found in live smoke: FastAPI's native `Query(ge=0)` validation returned `{"detail": [...]}` instead of the project envelope, so `min_viewers` is now validated in-body and returns `{"error": {"code": 422, ...}}` like every other search error. Pinned by test.
  - Live: `?q=storm` → 3 (lang en, viewers 5231/None/None); `&language=ja` → 0 (absent doesn't masquerade as a match); `&min_viewers=1000` → 1 (the 5231 record; None-viewer excluded); `&min_viewers=-5` → 422 envelope; filter variants cached separately (`cache_size: 4`)
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: `f57bb28 feat: sprint 8.1 search filters (...)` (+ merge `a13e460`)

## 2026-10-08 — Sprint 8.2 Map Experiment

- Sprint: 8.2 (Goal: decide whether geographic visualization adds meaningful value)
- Branch: `feat/8-2-map-experiment`
- What: `app/search/geo.py` (confidence tiers `exact` = platform coordinates, `derived` = our own deterministic gazetteer resolution of free-text `location_text`, `unlocated`; `GeoMarker`/`GeoCluster`/`CoverageReport`; haversine distance; single-linkage clustering at 50km; unweighted centroids); `GET /api/geo?q=` prototype endpoint returning markers + clusters + measured coverage. Deliberately NOT wired to any UI — instrumentation, not a feature.
- Non-goals (deferred): map UI components; a real geocoder (network lookup) — the gazetteer is documented as a *guess*, not a fact; per-cluster event semantics (6.3 already ruled clustering untrustworthy).
- Verification:
  - Backend: `python -m pytest -q` → **192 passed** (12 new in `tests/test_geo.py`: exact/derived/unlocated tiering, gazetteer token containment, unresolvable text, nonsense-coordinate rejection (untrusted platform data), coverage math + fractions, empty set, haversine known distances incl. antipode, cluster merge vs. split, singleton, mixed-confidence cluster merging, 422 envelope, live-coverage measurement); `python -m ruff check .` → clean
  - Frontend untouched (no contract change; experiment is backend/instrumentation): checks skipped
  - **Live measurement, the actual experiment**: `GET /api/geo?q=storm` → `total 3, exact 0, derived 0, unlocated 3`, 0 markers, 0 clusters. Empty `q` → 422 envelope.
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- **Verdict: the map does NOT ship in this product.** Measured geo coverage is **0%** in practice, by structure rather than by accident:
  - YouTube is the **only** coordinate source (`recordingDetails.location`) and rarely populates it for live streams;
  - Twitch reports **no** geodata at all;
  - the free-text `location_text` fallback only resolves against our own 12-place gazetteer, which is a documented guess and only helps for a handful of major places.
  - A map of 0 markers over 3 records is decoration, not discovery — and the roadmap correctly names this as an experiment whose only job was to reach a decision.
- What stays: `geo.py` + `GET /api/geo` as **instrumentation** (one endpoint, no new dependencies) so coverage can be re-measured if a future platform reports coordinates. Delete-on-evidence: if coverage stays 0% after Twitch ships, drop it.
- Known prototype simplifications (recorded, not fixed): unweighted centroids are skewed by latitude; single-linkage clustering can chain; mixed-confidence records cluster together even though one is a guess.
- Commit: `2a21b3c feat: sprint 8.2 map experiment (...)` (+ merge `84a8fff`)

## 2026-10-08 — Sprint 8.3 Mobile / Responsive Pass

- Sprint: 8.3 (Goal: usable on phones without a separate mobile app)
- Branch: `feat/8-3-mobile-responsive`
- Theme: **no toggle added** (confirmed with user — dark theme already works via `prefers-color-scheme` from Sprint 0.1 and OS-driven is the intended behaviour). One real dark-theme defect fixed: `.live-status--live` was hardcoded `#d92d20`, identical in both themes and dim on the dark surface. Now themed via `--live` (`#d92d20` light / `#ff6a5c` dark, same hue, lifted). Also removed dead Vite-demo CSS (`#social .button-icon`) from the dark media query.
- Responsive: removed the Sprint 0.1 fixed `1126px` `#root` frame that stranded the results grid in empty space (main was additionally capped at `640px` via an inline style) — replaced with a fluid `.app-main` (max 1120px, 16px gutters ≤640px); the inline style is gone so layout is testable/overridable.
- Touch: `@media (pointer: coarse)` gives interactive controls `min-height: 44px` (Apple/Google tap-target floor) — previously ~30–40px — with the report button full-width; `.stream-actions` children flex to fill on ≤640px so links are thumb-sized, not text-sized.
- Playback: `components/WatchModal.tsx` full-screen embed player as the roadmap's "optional full-screen playback" — Watch is now a button that opens the modal instead of a new tab. Modal locks background scroll, closes on Escape/backdrop/button, moves focus to the close button on open and restores it on close (inner clicks stopPropagation), strict `referrerPolicy`, `allowFullScreen` + `allow` for playback affordances, iframe never rendered outside the modal (discovery stays separate from playback).
- Non-goals (deferred): theme toggle (decided against), theme persistence across sessions (nothing to persist), swipe gestures, native app.
- Verification:
  - Frontend: `npm run typecheck` OK; `npm run lint` (oxlint) clean; `npm run test` → **46 passed** (7 new WatchModal tests: labelled iframe + referrerpolicy, focus on open, Escape, backdrop vs inner click, scroll lock, channel-name fallback; 2 new card tests incl. Watch-is-a-button + absent-when-unsupported; 1 new App modal open/close test; card/ResultsList tests updated for the button contract); `npm run build` OK; dev server → HTTP 200
  - Backend untouched (no contract change): checks skipped
  - Secrets: staged leak check empty; no `.env`/creds tracked
- Note: remaining responsive fidelity (44px targets on a real touch device, dark-mode readability of `#ff6a5c`) is inherently visual and stays a manual check — the CSS + components are asserted, the pixels are not.
- Commit: `1ff8ce7 feat: sprint 8.3 mobile/responsive pass (...)` (+ merge `ca18eea`)

## 2026-10-08 — Sprint 9.1 Kick Feasibility (research only, no adapter)

- Sprint: 9.1 (Goal: go/no-go decision backed by current technical information)
- Branch: `feat/9-1-kick-feasibility`
- What: `docs/kick-feasibility.md` — a decision doc, not code. No adapter written (that is 9.2, and it needs credentials).
- Key findings:
  - Kick ships an **official Public API** (`api.kick.com`, `docs.kick.com`, KickEngineering/KickDevDocs, Apache-2.0 OpenAPI) — legitimate documented access, no scraping required.
  - **No text search over stream titles** (same structural limit as Twitch Helix); discovery must be category-mediated: `GET /public/v1/categories?q={search word}` (q required) → `GET /public/v2/livestreams?category_id=...` (≤25 ids, ≤25 languages, limit ≤1000, cursor pagination). Fallback to unfiltered top-live.
  - `/public/v1/users/livestreams` (≤100 broadcaster user ids) gives a clean re-verify path for the Sprint 4.3 refresh contract.
  - `GET /public/v1/channels?slug=` returns `stream.{is_live, viewer_count, start_time, language, thumbnail, url, custom_tags, is_mature}` — everything the normalized model needs except geo, which is absent from the entire API.
  - Auth: **App Access Token via client_credentials** at `id.kick.com/oauth/token`; livestreams/categories need no user scopes — same pattern as the Twitch adapter. Requires registering an app in the Kick dev portal (credentials gate).
  - Rate limits exist and are enforced with 429; **exact numbers not published** — to be discovered empirically with a conservative budget at implementation.
- **Verdict: GO** for Sprint 9.2, gated on credentials exactly like Twitch. Playback embed details (player URL / parent-domain restriction) and mature-content policy (`is_mature` present per stream) are the two open items to settle during implementation; recommended default is to omit mature streams.
- Non-goals (deferred): the adapter itself (9.2); live verification until credentials exist; mature-content policy decision (flagged, not made).
- Verification: none applicable — research/documentation only, no code changed. `git status` confirms no source touched.
- Commit: `b565863 docs: sprint 9.1 kick feasibility research (GO, official public API)` (+ merge `9b3d167`)

## 2026-10-08 — Sprint 9.2 Kick Adapter (live verify deferred)

- Sprint: 9.2 (Goal: third platform, if 9.1 supports it)
- Branch: `feat/9-2-kick-adapter`
- What: `app/adapters/kick.py` (`KickAdapter`) — official Public API only, mirroring the Twitch adapter's structure:
  - App Access Token via `client_credentials` at `id.kick.com/oauth2/token`, cached until 60s before expiry, refreshed once on 401;
  - discovery `GET /public/v1/categories?q={topic}` → `GET /public/v2/livestreams?category_id=[...]` (≤25), unfiltered top-live fallback when no category matches;
  - `GET /public/v1/users/livestreams?broadcaster_user_id=[...]` (≤100) for the 4.3 refresh contract;
  - channel-stable `platform_stream_id` (broadcaster user id) so refresh + dedup behave;
  - configurable `KICK_CLIENT_ID/SECRET/MAX_RESULTS/MAX_CATEGORIES/EMBED_PARENT`; participates in the yt/twitch/kick/fakes factory matrix, never mixed with fakes.
- Field-shape honesty: Kick's published livestream payload varies across revisions, so mapping reads go through `_first` (first present key wins) and `_nested` for nested-vs-flat shapes. A rename degrades to fewer results, not a crash. `tests/test_kick.py` pins both shapes we know, and the docstring says plainly that live field names must be confirmed against the real API.
- Bugs caught by writing the tests (not by review):
  - `language` was buried in `metadata`, which would have silently broken the Sprint 8.1 language filter for Kick — now a first-class field;
  - flat `category_name` (non-nested shape) was unmapped.
- Non-goals (deferred): live verification until credentials exist; mature-content policy (`is_mature` recorded in metadata, NOT surfaced — flagged in 9.1, decision still open); v1→v2 endpoint migration (v1 categories is deprecated but is the only text-search variant).
- Verification:
  - Backend: `python -m pytest -q` → **204 passed** (12 new in `tests/test_kick.py`: full mapping incl. language/tags/embed-parent/absent-geo, category-q then category_id livestreams, top-live fallback, reverify live/offline, token caching, 401 refresh, 429 controlled error, config errors, legacy field-shape variant, factory matrix, service validation, configurable parent); `python -m ruff check .` → clean
  - Frontend untouched (no contract change): checks skipped
  - Live (no-cred): app boots, `GET /api/health` 200, `?q=storm` → 3 fake-platform results — Kick correctly absent without credentials; stats consistent; smoke `.db` removed after
  - Environmental note: the first smoke attempt hit a *different local project's* server holding port 8000 (`C:\Users\j\Projects\matrix`), which produced a confusing `KeyError: 'count'`. Re-ran on port 8011 after confirming the bind failure in the server log. Worth remembering: check `Get-CimInstance Win32_Process` for port conflicts before trusting a smoke result.
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Deferred live procedure (needs `KICK_CLIENT_ID/SECRET`): set in `backend/.env`, restart, `GET /api/search?q=` for topics with Kick coverage → expect `platform: "kick"` records, each verifiably live; open `source_url` to confirm; check the real field names against the mapped ones and adjust `_first` key lists if Kick sent different keys.

- Commit: `e960fef feat: sprint 9.2 kick adapter (official public api, mock-first)` (+ merge `e8bf0c1`)

## 2026-10-09 — Sprint 10.1 Platform Failure Isolation

- Sprint: 10.1 (Goal: a broken platform should not break the search engine)
- Branch: `feat/10-1-failure-isolation`
- Problem before: `SearchService.search` re-raised the first `AdapterError`, so one
  unavailable platform turned the entire search into a 502, and the route had no way
  to report which platform failed.
- What: per-adapter try/except in the service — a failing platform records a
  `PlatformStatus` entry and the loop continues with the healthy adapters. Every
  response now carries `platform_status` (healthy platforms included, so a client can
  say "N of M platforms"). The route returns 502 only when every platform failed and
  there are no results; a partial outage returns 200 with the healthy platforms'
  results intact. Degraded responses are never cached, so failures stay immediately
  retryable rather than being pinned for the TTL. `PlatformNotice` renders the warning
  in the UI. Adapter error messages surface by design (`AdapterError` is documented
  to never carry secrets), capped at 200 chars, and the total-outage 502 envelope
  itself stays opaque.
- Non-goals (deferred): retries/backoff per failure (currently single-attempt),
  circuit breaking, status persistence, alerting (10.3).
- Verification:
  - Backend: `python -m pytest -q` → **215 passed** (11 new in
    `tests/test_failure_isolation.py`). Each roadmap failure mode — timeout,
    quota-exhausted (403), rate-limited (429), auth failure (401), malformed
    response, connection outage, and misconfiguration — is simulated alongside a
    healthy adapter and must leave the healthy platform's results intact with an
    `error` status for the broken one. Also pins: empty results are not an error,
    all-platforms-failing reports all errors, degraded responses are not cached while
    healthy ones are, partial outage returns 200, total outage is the opaque 502,
    genuinely empty is 200, detail capped at 200 chars, and the 502 body never echoes
    adapter detail.
  - Frontend: `npm run typecheck` OK; `npm run lint` (oxlint) clean; `npm run test` →
    **50 passed** (4 new PlatformNotice tests + 1 App integration test; existing
    mocks updated for the new required `platform_status` field); `npm run build` OK
  - Live: `?q=storm` → 3 results with both fake platforms `ok`; empty `q` → 422
    envelope; smoke `.db` removed after
  - Process note: a scripted multi-line edit to App.test.tsx silently swallowed
    closing braces (parse error caught it), and the single-line variants were missed
    (tsc caught those). Reverted and redid it as a targeted regex insertion — the
    lesson is that bulk text edits to test fixtures need typecheck immediately after.
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: (this worklog entry pending)

## 2026-10-09 — Sprint 10.2 Rate Limiting & Abuse Protection

- Sprint: 10.2 (Goal: protect the service and platform API quotas)
- Branch: `feat/10-2-rate-limiting`
- What:
  - `services/ratelimit.py` — in-memory sliding-window limiter (per scope + client), thread-safe, unknown scopes fail open so a missing rule never takes the service down.
  - `api/deps.py` — `client_key` (peer address; `X-Forwarded-For` deliberately ignored so buckets can't be spoofed), `rate_limit(scope)` dependency, `validated_query` dependency.
  - `api/queryguard.py` — structural abuse guards: 200-char cap, control characters, repeated filler. Rejections log length + SHA-256 digest, never the raw query.
  - Routes: `/api/search` and `/api/geo` limited + query-validated; `/api/refresh` limited tightly (2/5min); `/api/health` intentionally unlimited so monitoring survives an abusive client.
  - `main.py` — logging configured (INFO, timestamps) so the above is actually visible.
  - Frontend: surfaces the server's `error.message` instead of `search failed: 429`.
- Config: `RATE_LIMIT_SEARCH=60`, `RATE_LIMIT_SEARCH_WINDOW=60`, `RATE_LIMIT_REFRESH=2`, `RATE_LIMIT_REFRESH_WINDOW=300`.
- Non-goals (deferred): **auth on /api/refresh** (still owed before public exposure — the limiter makes it expensive, not safe); per-account limits; adaptive/heuristic abuse rules; content filtering (11.2's job, deliberately not built).
- Verification:
  - Backend: `python -m pytest -q` → **227 passed** (12 new in `test_ratelimit.py`). Burst tests: 4-request burst against limit-3 returns `[200,200,200,429]`; X-Forwarded-For spoofing does NOT buy a new bucket; refresh limited to 2/300s; health never limited; unknown scope fails open. Query guards: >200 chars, control chars, and repeated filler all 422; normal queries pass. Privacy: `PRIVATE_USER_INPUT_…` never appears in logs while `digest=` does. Includes a hermetic-limiter fixture with a note about why (the limiter is process-global and starved other suites at first).
  - Frontend: `npm run typecheck` OK; `npm run lint` clean; `npm run test` → **51 passed** (new test asserts the rate-limit message surfaces and `429` does not); `npm run build` OK
  - Live: normal search 200 with `platform_status`; **70-request burst → 59×200 then 11×429** with the envelope body; health 200 throughout; 300-char query rejected
  - Secrets: staged leak check empty; no `.env`/creds tracked
- Known limitation recorded: the limiter is per-process. With multiple uvicorn workers the effective limit multiplies; Redis (or another shared store) is the fix, and stays unjustified until horizontal scaling actually happens.
- Commit: (this worklog entry pending)

## 2026-10-09 — Sprint 10.3 Observability

- Sprint: 10.3 (Goal: know whether the index is actually healthy)
- Branch: `feat/10-3-observability`
- What: `app/services/metrics.py` — thread-safe in-process `MetricsRegistry` tracking all eight
  roadmap quantities, plus `observability_snapshot()` composing live counters + durable store
  health. `GET /api/stats` now returns the full dashboard.
  - searches / cache hits+misses+hit_rate (recorded through the real search path)
  - per-adapter requests, errors, avg/last latency, last error
  - `adapter_error_rate` computed over **all attempts** (success + failure) so a total outage
    reads 1.0, not a misleading 0.0 — a real bug found while testing
  - streams_discovered vs streams_indexed — discovery is a fresh insert (`first_seen_at ==
    last_seen_at`), a re-sighting is not; found and fixed during verification
  - estimated_quota_units from adapters' new `search_quota_cost` declaration (YouTube 101 =
    search.list 100 + videos.list 1; Twitch/Kick 0, request-limited rather than quota-limited)
  - index staleness: total / live / ended / stale / fresh / unverified / unknown
  - report volume; a broken report store degrades to `-1` instead of breaking the dashboard
- Non-goals (deferred): UI dashboard (a JSON endpoint is inspectable and the product stays
  discovery-focused), time-series/Prometheus/OTel, remote alerting.
- Verification:
  - Backend: `python -m pytest -q` → **238 passed** (11 new in `test_observability.py`, each
    asserted through the real search path rather than in isolation: searches+cache, latency,
    failures, discovered-vs-indexed, quota estimate, request-limited platforms, stale/fresh
    index buckets, report volume, composite snapshot, registry reset, and a degraded report
    store). The stats-shape test in `test_cache.py` was rewritten to assert the new payload.
  - Live dashboard inspection (the roadmap's verification): 2 searches + 1 report →
    `searches: 2, api_requests: 4, adapter_requests: 4, errors: 0, streams_discovered: 3,
    streams_indexed: 6, index {total/live/fresh: 3, stale/unverified/ended: 0}, reports: 1`,
    per-adapter latency populated. Every number internally consistent.
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Known limits recorded: counters are per-process (same caveat as the rate limiter); latency
  includes only synchronous adapter time, not HTTP/SQLite waits; quota is an estimate from
  documented rates, not observed platform accounting.
- Commit: (this worklog entry pending)

## 2026-10-09 — Sprint 11.1 Source and Content Handling Review

- Sprint: 11.1 (Goal: make the indexing boundary explicit)
- Branch: `feat/11-1-content-boundaries`
- What: `docs/content-boundaries.md` — a review, not an aspiration. Each of the seven roadmap
  areas is marked **enforced** (verified by reading the implementation and, where possible, by a
  test) or **documented gap**.
- Verification performed by reading code, not by trusting it:
  - No media anywhere: grep for `yt-dlp|download|.mp4|write_bytes|createObjectURL` finds nothing
    in backend or frontend. The `streams` table has no BLOB column; `thumbnail_url` holds a URL.
  - Embed gating: `StreamCard` requires `embed_supported && embed_url`; the iframe exists only
    inside `WatchModal` (never in a card or list).
  - No proxy: the OpenAPI paths contain no proxy/fetch route at all.
  - Attribution: every Stream carries `platform`/`channel_name`/`source_url`, rendered as a
    `PlatformBadge` + Open Source link.
- Gaps found and recorded honestly:
  - **No takedown/removal path exists.** The only deletion in the codebase is the
    `DELETE FROM streams WHERE live_status='ended' AND last_seen_at < cutoff` prune (4.3). There
    is no `DELETE /api/streams/{id}`, no rights-holder intake, no suppression of a specific
    result. Suggested minimal follow-up is written into the doc.
  - `is_mature` is recorded in metadata by Twitch/Kick/YouTube adapters but **not surfaced** —
    an open product decision, flagged again here rather than decided.
  - Reports are stored but not acted on (advisory only).
- Tests: `tests/test_boundaries.py` (7 new) pins the structural claims so the doc can't
  silently drift — no media-payload fields on the model, index round-trip is metadata-only,
  embed-only-when-allowed, no proxy route in the OpenAPI schema, reports don't remove content,
  the doc itself must still admit the takedown gap, and `is_mature` stays metadata-only.
- Verification:
  - Backend: `python -m pytest -q` → **245 passed**; `python -m ruff check .` → clean
  - Live review (roadmap's check): `?q=wildfire` → every result names its platform and links to
    the platform's own domain; `twitch/rivercam` embed-supported, `twitch/cityhall` and
    `fake/…` are not, so the UI correctly offers Watch vs Open Source per record.
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Commit: (this worklog entry pending)

## 2026-10-09 — Sprint 11.2 Search Abuse Controls

- Sprint: 11.2 (Goal: prevent search becoming a mechanism for abusive targeting)
- Branch: `feat/11-2-search-abuse`
- Framing: the roadmap says *evaluate, implement only controls justified by observed/product
  requirements*. This sprint is a documented evaluation plus **one** implemented control, not a
  content-moderation system.
- Evaluation of all five areas (findings verified in code, not assumed):
  - **Spam queries** — already controlled in 10.2 (200-char cap, control chars, repeated filler,
    rate limit). Verified live: 400-char → 422, `bad\x01query` → 422, legit query → 3 results.
  - **Malicious metadata** — frontend has no `innerHTML`/`dangerouslySetInnerHTML` (scanned every
    `.tsx`), React escapes title/channel/description; backend stores verbatim and uses
    parameterized/static SQL. Channel titles are attacker-controlled text, so this matters —
    already safe by construction.
  - **Doxxing-style searches** — result surface is public broadcasts only (title/channel/
    viewers/thumbnail). No accounts, no cross-search profile, no PII beyond ephemeral bucketing.
    No control built: intent detection needs content classification, which is out of scope for an
    index.
  - **PII exposure** — queries never persisted (request scope + 60s in-memory cache, digest-only
    logging from 10.2). **One real gap found: raw client IPs written to logs** on rate-limit
    rejection, indefinitely retained.
  - **Platform-specific abuse** — intent, not signal. Out of scope; the report button (2.3) is
    the user-facing path.
- Implemented: `mask_ip()` in `app/api/deps.py` — logs keep the /24 (IPv4) or /64 (IPv6) prefix
  plus an 8-char digest, dropping the host part. In-memory bucket key unchanged, so rate-limit
  behaviour is identical. Rationale in the docstring.
- Tests: `tests/test_abuse.py` (15 new) — no `innerHTML` in any `.tsx`; payload metadata
  round-trips verbatim (never interpreted); queries/metrics never persist query text; a rejected
  over-limit query never leaks its marker to logs; raw IPs never appear in logs while prefix +
  correlation survive; IPv4/IPv6/malformed masking; spam rejected vs legit queries allowed (incl.
  short repeats like "go go go"); no history/queries endpoint; `/api/stats` leaks no client
  identity.
- Verification:
  - Backend: `python -m pytest -q` → **260 passed**; `python -m ruff check .` → clean
  - Live: 400-char → 422 envelope; control chars → 422; legit → 3 results; rate-limit burst
    behaved; logs show `query rejected: too_long len=400 digest=…` and `… control_chars digest=…` —
    no raw query text, no raw IPs
  - Secrets: staged leak check empty (incl. `.db`); no `.env`/creds tracked
- Decision recorded: what was deliberately NOT built — keyword blocklists, content classifier,
  `is_mature` filtering (still open from 9.2), and query logging for "abuse forensics" (which
  would itself be the privacy violation).
- Commit: (this worklog entry pending)

## 2026-10-09 — Sprint 12.1 TikTok Feasibility (research only, no adapter)

- Sprint: 12.1 (Goal: decide whether TikTok can be integrated legitimately and sustainably)
- Branch: `feat/12-1-tiktok-feasibility`
- What: `docs/tiktok-feasibility.md` — decision record. No adapter written (and none will be,
  absent a change on TikTok's side).
- Findings:
  - TikTok's official platform exposes: Research API, TikTok API v2 (`/v2/video/query/`),
    Content Posting API, Display API.
  - **Research API is the closest option and still a dead end**: eligibility is limited to
    "independent and academic researchers who conduct research on a not-for-profit basis", and it
    is **VOD-only** — the video codebook has creation time, likes, comments, subtitles, duration,
    view count; there is no live status, live start time, or live viewer count.
  - **TikTok API v2 / Display / Content Posting are creator-scoped**, not platform-scoped:
    `video.query` verifies the videos "belong to the user". No platform-wide search or live
    listing exists.
  - **All actual TikTok LIVE access is undocumented** — open-source clients reverse-engineer
    TikTok's internal Webcast/signing services and their own docs state "TikTok does not offer a
    public official API for reading livestream events"; paid third-party services wrap the same
    endpoints and are explicitly unaffiliated with TikTok.
  - **Deeper mismatch independent of legality**: every available tool is creator-keyed — you
    connect to a username you already know. There is no "live broadcasts about X" query anywhere,
    so an event-first product would have nothing to search even if ToS risk were acceptable.
- **Verdict: NO-GO.** Adapter stays deferred. This is the same flip-condition recorded in
  `docs/kick-feasibility.md` ("findings that undocumented access would be required").
- Re-evaluation criteria written into the doc: an official API with live-stream search/listing,
  access for non-academic developers, live status + start time + viewer count in responses, and
  documented embedding permissions.
- Verification: research/documentation only — no code changed, `git status` confirms nothing else
  touched. Full suite (260 tests) still green as a no-regression check.
- Secrets: n/a, nothing staged.
- Commit: (this worklog entry pending)

## 2026-10-10 — YouTube Live Verification (deferred from Sprints 1.2 / 1.3 / 5.x)

- Goal: close the deferred source-truth procedure for the YouTube adapter with a real key.
- Setup: user added `YOUTUBE_API_KEY` to `.env` (project root). Verified before use: `.env`
  exists, is gitignored (`.gitignore:21`), and untracked by git; the key value was never printed
  or committed. Loaded into the server with `uvicorn --env-file ../.env`.
- Procedure (from `README.md`): 5 queries — wildfire, storm, news, gaming, concert.
- Results (each query → 10 records, all `platform: youtube`, all `live_status: live`):
  - `wildfire` — LA County Fire live scanner, storm-chaser severe-weather coverage
  - `storm` — AccuWeather Hurricane Isaias live, storm-chase streams (9492 / 5357 / 2465 viewers)
  - `news` — Television Jamaica Prime Time News, Bloomberg Business News Live
  - `gaming` — streamer gaming streams (1120 / 289 / 78 viewers)
  - `concert` — Mosaic Concert (Boyer College of Music), A&M-Kingsville bands, Notre Dame Symphony Orchestra
- Source-truth checks from the roadmap, all passing:
  - results appear ✓ (10 per query)
  - titles match source ✓ (real YouTube live titles; channel names match the broadcasting channel)
  - thumbnails match source ✓ — `https://i.ytimg.com/vi/<id>/hqdefault_live.jpg`, fetched and returns HTTP 200 from the YouTube CDN
  - links open the live broadcast ✓ — `https://www.youtube.com/watch?v=<id>` returns HTTP 200
  - platform identified ✓ (all `youtube`)
  - no raw API response leaks ✓ — response field set is `Stream`-only; no `snippet` /
    `liveStreamingDetails` / `recordingDetails` / `etag` / `pageInfo`
- Additional real-data validation:
  - identity: `id=youtube-<videoId>`, `source_url`/`embed_url` correctly assembled from the video id
  - `started_at` from `liveStreamingDetails.actualStartTime` (e.g. 2026-09-30 for a 24/7 stream, 2026-10-09 for the live concerts) and `freshness: fresh`
  - viewer counts present and plausible; ranking put the title-matching stream first even at 1
    viewer, confirming the Sprint 7.3 decision (viewers as tiebreak, never primary) behaves as
    intended on real data
  - frontend + backend served together (frontend 200, backend real results, thumbnails from
    `i.ytimg.com`)
- Quota observed: ~5 searches × ~101 units ≈ 505 units of YouTube's daily quota.
- Still pending the same treatment: `TWITCH_CLIENT_ID/SECRET` (Sprint 5.2) and
  `KICK_CLIENT_ID/SECRET` (Sprint 9.2) — both recorded as deferred in their worklog entries.
- Secrets: key never printed or committed; git confirms it is in no tracked file.
- **False-positive correction:** a first log scan reported the key present in uvicorn's
  `boot.err`. Re-checked three ways — `--env-file` alone, `--env-file --reload`, and a
  fresh `[System.IO.File]::ReadAllText(...).Contains(key)` check — and the key is **not**
  in the logs; uvicorn only logs `Loading environment from '<path>'`. The original scan was
  faulty: it passed both `-Pattern [regex]::Escape($key)` and `-SimpleMatch` to
  `Select-String`, a contradictory combination that produced a false positive. Lesson: for
  secret scanning use an exact `Contains()` check, never that flag combination. The stray
  log files were deleted and the repo re-verified clean.

## 2026-10-10 — Sprint 13.1 Caption/Transcript Relevance

- Sprint: 13.1 (Goal: determine whether transcript indexing is practical and useful)
- Branch: `feat/13-1-transcript-relevance`
- What: `docs/transcript-relevance.md` — evaluation, no code. Nothing was built.
- Motivating case: the `vague-title` gap from Sprint 7.1 (a stream titled "LIVE" is unrankable by
  any text ranker). A transcript would supply the missing text.
- Blocking finding (primary-source):
  - YouTube's documented `captions.download` reference states verbatim: **"This method requires
    the user to have permission to edit the video."** It also requires OAuth 2.0 (not an API key)
    and carries a quota cost of **200 units**; `captions.list` (track IDs) is another **50 units**
    and also OAuth required.
  - Consequence 1 — **not third-party**. StreamSearch discovers streams broadcast by other
    channels; an API key cannot download them, and we are never the owner, so every transcript
    worth indexing is inaccessible.
  - Consequence 2 — **not cheap**. 250 units/stream would exhaust the daily quota almost
    immediately at discovery-corpus scale.
  - No alternative documented path: `videos.list?part=contentDetails` exposes only a boolean
    `contentDetails.caption` flag, never text. Auto-generated captions get no exemption.
  - The only remaining access is undocumented player/timedtext endpoints — the same
    reverse-engineered boundary ruled out for TikTok in Sprint 12.1, so not an option.
- Consequence for the gap: `vague-title` stays open and stays honestly labelled as the one 7.1
  failure class that cannot be closed legitimately (no text for keyword; no signal for semantic;
  no legitimate access to the one text source that could help). Noted that the best available
  behaviour is to lean on the other fields and show the creator, not pretend to know the topic.
- **Verdict: NO-GO.** Re-evaluation criteria written into the doc (documented API for videos you
  don't own; cost compatible with a live corpus; terms permitting index-by-search).
- Verification: research/documentation only — no code changed, `git status` confirms nothing else
  touched; full suite re-run green as a no-regression check (260 tests).
- No secrets involved.
- Commit: (this worklog entry pending)
