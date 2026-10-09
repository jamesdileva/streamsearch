# Source and Content Handling Boundaries (Sprint 11.1)

> The system is an **index/discovery layer, not an archive or broadcaster**.
> This document states what StreamSearch does and does not do with source
> content, and — importantly — where the boundaries are still incomplete.

Each section notes whether the boundary is **enforced in code** (verified by
reading the implementation, and where possible by a test) or **documented
only**. Where it is only documented, that is stated plainly rather than
implied.

---

## 1. Source attribution

**Every result carries its platform and a link back to the source.** `Stream`
stores `platform`, `channel_name`, `source_url`, and the UI renders a
`PlatformBadge` plus an **Open Source** button linking to the originating
platform (never to a StreamSearch-hosted copy).

- Status: **enforced**. `resolve_marker`/`StreamCard` derive both from
  normalized fields; there is no path that renders a result without its
  platform identity.
- Roadmap check: "review representative results and ensure the UI accurately
  identifies the originating platform" — done on the live app (see worklog);
  with fake adapters the badge reads `fake`/`twitch`, and with real
  credentials it reads `youtube`/`twitch`/`kick` from the adapter's declared
  `platform`, never from a string the platform sends in its payload.

## 2. Embed behaviour

Embeds are the **only** way playback happens, and only when the platform
permits it.

- Embeds render only when `embed_supported` is true AND `embed_url` exists
  (`StreamCard.tsx` gates the Watch button on both). Otherwise the UI offers
  "Open Source" only.
- The embed iframe renders **only inside `WatchModal`** — never in the card,
  never in a list. Nothing is iframed until the user asks.
- The iframe uses a strict `referrerPolicy` and no `allow-*` beyond playback
  affordances. The embed parent domain is configurable
  (`TWITCH_EMBED_PARENT`, `KICK_EMBED_PARENT`) because both platforms
  restrict embeds to declared parent domains.
- Status: **enforced in code and covered by tests** (Watch present/absent per
  `embed_supported`; modal attributes).

## 3. External links

- All "Watch" and "Open Source" actions are plain links/iframes to the
  platform. There is no URL shortener, no click tracking, no redirect
  through StreamSearch.
- We do **not** proxy arbitrary URLs. The API has no generic fetch/proxy
  endpoint — the only outbound HTTP in the codebase goes to the documented
  platform APIs from the adapters (verified by grep: no proxy routes).
- Status: **enforced**.

## 4. Prohibited local storage

**We store discovery metadata only.** Verified by reading `index.py`:

- The `streams` table columns are all `TEXT`/`INTEGER`/`REAL` metadata
  (identity, title, description, `thumbnail_url`, `source_url`, `embed_url`,
  statuses, timestamps, counts, tags, geo, JSON `metadata`).
- `thumbnail_url` holds a **URL reference**, not image bytes. No BLOB column
  exists.
- The frontend never converts responses to blobs
  (no `createObjectURL`, no download attributes — verified by grep).
- No video, audio, or media is requested or written anywhere in the codebase.

Status: **enforced**. This is the core legal boundary of the product.

## 5. Reporting

Users can report bad data from any result card: **Broken link / No longer
live / Wrong topic / Other** → `POST /api/reports`, persisted in SQLite,
counted in observability (`/api/stats`).

- Status: **enforced** (Sprint 2.3).
- Gap: reports are stored but **not yet acted on automatically** — no
  workflow removes or re-verifies a stream because it was reported. This is
  documented as a known limitation, not a working moderation pipeline.

## 6. Platform takedown / removal handling

**This boundary does not exist yet.** The honest status:

- What *does* happen: the refresh pass (Sprint 4.3) calls
  `reverify`, and a platform confirming a broadcast is gone transitions the
  record to `ended` and prunes it after the retention window. A user report
  or a repeated failed re-verification is the only other signal.
- What does *not* happen:
  - no endpoint to remove a record on request (there is no
    `DELETE /api/streams/{id}`);
  - no takedown intake from a platform or rights-holder;
  - no way to suppress a specific result manually;
  - ended records remain in the index (visible via `GET /api/geo` coverage
    and stats) until the prune window passes.

Status: **partial / documented gap**. The roadmap asks for takedown
handling to be documented; it is documented here as *absent*, because
pretending otherwise would be worse than admitting it. Suggested minimal
follow-up (not built): a `DELETE /api/streams/{id}` plus an "ended +
confidential" state that hides rather than waits for pruning.

## 7. Disturbing thumbnails / content

Thumbnails are displayed as-is from the source platform, because blurring
or filtering would require us to hold and inspect media (see §4) and would
be a content decision this index has no basis to make.

- Status: **documented, with one partial technical control**: adapters
  record `is_mature` where the platform reports it (Kick/Twitch/YouTube),
  and it is currently **metadata only — not surfaced in the UI**.
- Open decision (flagged in Sprint 9.2 and still open): whether to filter,
  blur, or label `is_mature` results. Not made here, because it is a product
  policy call, not a technical one.
- Nothing else screens content. Search returns what the platform matches.

---

## Summary table

| Area | Status |
|---|---|
| Source attribution | Enforced |
| Embed behaviour | Enforced + tested |
| External links | Enforced (no proxy) |
| Prohibited local storage | Enforced (metadata only) |
| Reporting | Enforced (but not acted on) |
| Takedown / removal | **Not implemented — documented gap** |
| Disturbing content | Documented; `is_mature` captured, not surfaced |
