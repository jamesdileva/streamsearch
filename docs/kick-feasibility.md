# Kick Feasibility Research (Sprint 9.1)

> Decision doc for whether to add a Kick adapter (Sprint 9.2). Researched
> 2026-10-08 against Kick's official Public API. Scraping was NOT assumed
> acceptable — this documents only documented, legitimate access.

**Verdict: GO** — implement the adapter in Sprint 9.2, gated on Kick
API credentials exactly as Twitch's adapter is. Evidence below.

---

## 1. Available discovery mechanism

Kick ships an **official Public API** (`api.kick.com`, documented at
`docs.kick.com`, source in `github.com/KickEngineering/KickDevDocs`,
Apache-2.0 OpenAPI spec). This is a real, supported API — not an
undocumented endpoint or screen-scraping.

Critical property for an event-first search engine: **there is no
text search over stream titles** (same limitation as Twitch Helix).
Discovery must go through *categories*:

| Step | Endpoint | Notes |
|---|---|---|
| 1. Topic → categories | `GET /public/v1/categories?q={search word}` | **`q` is required**; up to 100 results/page. This is a text search over category names — the key capability. |
| 2. Categories → live streams | `GET /public/v2/livestreams?category_id=...` | `category_id` accepts **up to 25 ids**; `language_code` up to 25; `limit` up to 1000; cursor pagination; `sort` by viewer_count or started_at. |
| 3. Fallback | `GET /public/v2/livestreams` (no filter) | Top live streams when no category matches, so arbitrary topics still return candidates for ranking. |
| Re-verify | `GET /public/v1/users/livestreams` | **By broadcaster user id (up to 100)** — the `reverify` path for the Sprint 4.3 refresh contract. |

`GET /public/v1/categories/{id}` returns tags + `viewer_count` for a
single category. `GET /public/v1/channels?slug=...` (up to 50 slugs)
resolves a channel by name and includes its `stream` sub-object.

## 2. Live status

Explicit and reliable:

- `livestreams` endpoints return only **currently active** streams
  ("Get active livestreams… sorted from oldest to newest").
- `channels` response carries `stream.is_live`, `stream.viewer_count`,
  `stream.start_time`, `stream.language`, `stream.thumbnail`,
  `stream.url`, `stream.custom_tags`, `stream.key`, `stream.is_mature`.
- Re-verification by user id returns only live channels, so a missing
  channel maps cleanly to **ended** — matching the existing
  `reverify` contract (dict = live, None = gone, absent = unknown).

## 3. Metadata available for the normalized model

From `LivestreamV2` / channel `stream` objects:

| StreamSearch field | Kick source |
|---|---|
| `platform`, `platform_stream_id` | user/channel id (stable; Kick streams go offline rather than getting a new broadcast id) |
| `channel_id`, `channel_name` | `channel` / `broadcaster_user` |
| `title` | `stream_title` / livestream title |
| `description` | `channel_description` (only on channels endpoint) |
| `thumbnail_url` | `stream.thumbnail` |
| `source_url` | `stream.url` / channel slug URL |
| `embed_url` | Kick player URL — **parent/embed domain requirements must be verified at implementation** (see §6) |
| `live_status`, `started_at`, `viewer_count` | `stream.is_live`, `stream.start_time`, `stream.viewer_count` |
| `category` | `category.name` |
| `tags` | `stream.custom_tags` |
| `language` | `stream.language` (BCP-47) — already a normalized field since Sprint 8.1 |
| `latitude` / `longitude` / `location_text` | **not present anywhere in the API** (expected; geo coverage is already 0%) |

## 4. Playback / embeds

Kick supports iframe embeds via its player. **Unverified before
implementation:** the exact player URL and whether `parent`-style domain
restriction applies (as with Twitch). Treat as an implementation-time
check with a controlled test, and make the parent configurable
(`KICK_EMBED_PARENT`) mirroring `TWITCH_EMBED_PARENT`.

Policy-compatible: we link/embed the source; we never download or host
video. Unchanged from the product's core boundary.

## 5. Authentication & rate limits

- **OAuth 2.1**. For read-only discovery we need an **App Access Token**
  via the `client_credentials` grant at `https://id.kick.com/oauth/token`
  — the same pattern as the Twitch adapter (no user authorization, no
  interactive consent).
  - `livestreams` and `categories` explicitly work with App Access
    Tokens "with no special scope required".
  - Scopes (`channel:read`, `user:read`, …) exist for user-authenticated
    actions; we need none of them.
- Requires **registering an app** in the Kick developer portal to get a
  client id/secret — a credentials gate, exactly like `TWITCH_CLIENT_ID/SECRET`.
- **Rate limits exist and are enforced with HTTP 429** (community clients
  implement automatic retry-on-429, which implies it happens in practice).
  **Exact limits are not published/confirmed** — discover empirically
  during implementation with a conservative `max_results` budget, the
  same posture the YouTube adapter takes against quota cost.

## 6. Terms / constraints & risks

| Item | Assessment |
|---|---|
| Documented API | Yes, official, Apache-2.0 spec. No scraping needed. |
| Attribution / linking | Link + embed only; no video storage. Complies with the product boundary. |
| Mature content | `is_mature` is present per stream. Surfacing mature content is a **policy decision** that must be settled before 9.2 ships (filter, flag, or omit). Recommended: omit from results until decided. |
| Gambling-adjacent categories | Kick's catalogue includes heavy slots/casino content. Only matters if we later trust `category` for relevance; no action now. |
| API maturity | v1 endpoints are marked `deprecated` in favour of v2 in places; the OpenAPI is actively evolving. Mitigation: use v2 where it exists, keep the adapter's request shapes behind small private methods so endpoint swaps are local. |
| No title search | Same real limit as Twitch: topic discovery is category-mediated. Acceptable and already an established pattern; the relevance layer handles the rest. |
| Credentials | None held today → live verification deferred, same as YouTube/Twitch. |

## 7. Recommendation

**GO** for Sprint 9.2, with these gates:

1. Implement `KickAdapter` against `adapters/base.py` only — no new
   service contracts (the contract already survives 3 platforms).
2. Mirror the Twitch adapter's structure exactly: token cache, categories
   `q` search → livestreams by `category_id`, top-live fallback, reverify
   via `users/livestreams`.
3. Keep the stream id stable (user/channel id) so refresh + dedup behave.
4. `KICK_CLIENT_ID` / `KICK_CLIENT_SECRET` / `KICK_MAX_RESULTS` /
   `KICK_EMBED_PARENT` config; adapter participates in the same
   key-driven factory matrix, never mixed with fake adapters.
5. **Verify live only once credentials exist** — same deferred-verification
   pattern and worklog procedure as Sprint 5.2. Mocked tests in the
   sprint must cover mapping, category search, fallback, reverify,
   auth failure, and payload-shape drift.
6. Resolve the mature-content question before or during 9.2; do not
   surface `is_mature` streams by default.

## 8. What would change this verdict

- Kick requiring paid/approval-gated API access for public read data.
- Rate limits so tight that topic search becomes quota-prohibitive
  (would need request-budget + cache re-evaluation).
- Embedding restrictions that prevent in-product playback (drop Watch,
  keep Open Source — still useful).
- Findings that undocumented access would be required anywhere (would
  flip this to NO-GO and stay deferred, as with TikTok).
