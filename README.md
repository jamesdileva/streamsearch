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

Sprint 13.1 done — transcript relevance: **NO-GO** in `docs/transcript-relevance.md` (`captions.download` needs OAuth + owner-level edit permission, so third-party transcripts are not legitimately accessible).

Sprint 13.2 done — event detection works on live data; kept as an inspectable prototype (`GET /api/events?q=`), NOT wired to search. Recall 2/2 and precision 5/5 on the labeled set, and live YouTube `storm` grouped all 10 Hurricane Isaias broadcasts into one event. Verdict: keep prototype, don't ship as a ranking feature, pending a larger sample (`docs/event-detection.md`).

Sprint 13.3 — computer vision: **NO-GO without an experiment** — decoding frames violates the enforced metadata-only boundary of `docs/content-boundaries.md`, and small-VLM reliability plus GPU/cost make it unaffordable. Sprint 14.1 done — saved searches: re-save an existing query+filters, or run/remove it from the list. Persisted in `localStorage` under `streamsearch:saved-searches` (cap 25, corrupt entries fail soft, empty queries refused). No accounts — cross-device sync would need them and stays deferred per `architecture.md`. Sprint 14.2 live alerts deferred. Twitch/Kick live verification deferred pending their API keys.