# TikTok Feasibility Research (Sprint 12.1)

> Decision doc for whether to add a TikTok adapter. Researched 2026-10-09
> against TikTok's official developer platform. Undocumented access was not
> considered an acceptable option, per the product boundary.

**Verdict: NO-GO.** Do not build a TikTok adapter. Keep it deferred as a
future re-evaluation only.

---

## What TikTok officially offers

TikTok's developer platform (developers.tiktok.com) exposes these product
families:

| API | What it does | Live discovery? |
|---|---|---|
| Research API (`/v2/research/video/query/`) | Video metadata for approved academic researchers | **No** — VOD only |
| TikTok API v2 (`/v2/video/query/`) | Video details for the *authorized user's* own videos (`video.list` scope) | **No** |
| Content Posting API | Post on behalf of a creator | No |
| Display API | Embed the app user's own content | No |
| Research Tools (VCE) | Dataset access for vetted researchers | **No** |

## Why none of them work

### Research API — the closest option, still a dead end
- It is gated: "researchers must submit an application, be approved, and
  adhere to our TikTok Research Tools Terms of Service", and eligibility is
  limited to "independent and academic researchers who conduct research on a
  not-for-profit basis". A commercial discovery service does not qualify.
- It covers **recorded videos, not live streams**. The codebook's video
  fields are creation time, likes, comments, subtitles, duration, view
  count — there is no live-status, viewer-count, or started-at-live field.
  There is no way to answer "is this live?" or "is anything live about X?".

### TikTok API v2 / Display / Content Posting
- These are creator-scoped, not platform-scoped: `video.query` verifies that
  the videos "belong to the user". You can only read what the authenticated
  creator grants. There is no platform-wide search or live-stream listing at
  all.

## What exists instead — and why we are not using it

The only way to read TikTok LIVE data today is via **undocumented internal
endpoints**:

- Unofficial open-source clients (TikTokLive, tiktok-live-connector,
  and others) reverse-engineer TikTok's internal Webcast/signing services.
  Their own documentation states plainly: *"TikTok does not offer a public
  official API for reading livestream events."*
- Managed third-party services (tik.tools and similar) wrap the same
  reverse-engineered endpoints for a fee, and are explicitly "not affiliated
  with, endorsed by, or sponsored by TikTok or ByteDance".

Using these would mean:
1. Reverse-engineering and depending on undocumented endpoints that break
   whenever TikTok rotates signing or protocol;
2. Accepting a legal/ToS risk the product boundary explicitly rules out
   (`AGENTS.md`: "scraping is NOT assumed acceptable");
3. Building on data access the platform has chosen not to offer.

**Decision: no.** This is the same trap `docs/kick-feasibility.md` recorded
as a flip condition — "findings that undocumented access would be required
anywhere" — and it is the correct call here.

## The deeper mismatch (independent of legitimacy)

Even setting legality aside, TikTok LIVE access is **creator-keyed, not
discovery-keyed**: every available tool connects to a stream you already
know by username. There is no "find live broadcasts about wildfire" query
anywhere in the ecosystem.

StreamSearch is event-first search — the core question is "what is happening
right now about X". Even an unofficial adapter would require a discovery
primitive that simply does not exist, so the product value would be near
zero before weighing the risk.

## What would change this verdict

Re-evaluate only if **all** of these become true:
1. TikTok ships an official API exposing live-stream search/listing;
2. Access is available to non-academic developers (app credentials, not
   researcher approval);
3. Responses include live status, start time, and viewer count;
4. Embeds are permitted under documented rules.

Until then: NO-GO, documented as deferred.
