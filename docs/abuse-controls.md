# Search Abuse Controls — Evaluation & Decisions (Sprint 11.2)

The roadmap for 11.2 says: *evaluate these areas, implement only controls
justified by observed/product requirements*. This document records the
evaluation, what was implemented, and — equally important — what was
deliberately **not** implemented and why.

Guiding constraint: StreamSearch is an **index/discovery layer**, not a
moderation system. It has no accounts, no content classification, and no
basis for judging intent. Adding either without a demonstrated need would
make search worse (11.1) and expand the product's remit without evidence.

---

## 1. Spam queries

**Evaluated:** cache-busting, filler, oversized payloads, control characters.

**Already controlled (Sprint 10.2):** 200-char cap, control-character
rejection, repeated-filler detection, and rate limiting. Verified live:
a 400-char query returns 422, `bad\x01query` returns 422, legitimate
queries still work.

**Decision:** no further controls. There is no observed spam problem, and
the structural guards already prevent the one genuine cost — burning
platform quotas and cache space on junk.

## 2. Malicious metadata (platform-supplied)

**Evaluated:** XSS/injection via stream titles, channel names, descriptions,
tags, thumbnails, categories — all attacker-influenceable fields (a channel
name is attacker-chosen text).

**Findings:**
- The frontend has **no** `innerHTML` / `dangerouslySetInnerHTML` (verified
  by scanning every `.tsx`), so React escapes all platform metadata to
  text. A `<script>` title renders literally.
- The backend stores metadata as data, never interpreting it. No SQL is
  built by concatenation — all queries are parameterized or static.
- Thumbnails/link URLs are rendered as attributes, and `rel="noreferrer"`
  is set on external links. Note: `javascript:` URLs are not a vector here
  because `embed_url`/`thumbnail_url` are assembled by the adapter (not
  taken from platform text) and `source_url` is likewise constructed, and
  unsupported fields are absent.

**Implemented:** nothing new — the existing design already handles it.
Added `tests/test_abuse.py` so this stays verified (scan for
`innerHTML`; store/round-trip a payload verbatim).

## 3. Doxxing-style searches

**Evaluated:** someone searching for a private individual to locate their
stream, or to build a list of where a person appears.

**Findings:** the search surface is *public broadcasts only*. Results are
public stream metadata (title, channel, viewers, thumbnail). Nothing the
service returns is non-public. The service has no accounts and no
cross-search profile.

**What we do about it:** nothing, deliberately. Intent detection requires
either content classification (out of scope) or human review (no
capacity). The *mitigation that exists* is structural: queries are not
persisted, so the service cannot be interrogated for "what has someone
searched".

**Decision:** no control. Documented as accepted risk.

## 4. Personal information exposure

**Evaluated:** what PII does StreamSearch collect and retain?

| Data | Collected | Retained | Notes |
|---|---|---|---|
| Search queries | in request scope | in-memory cache only, 60s TTL | never persisted to disk |
| Search logs | digest only (Sprint 10.2) | logs | query text never written; length + SHA-256 prefix |
| Client IP | required as the rate-limit bucket key | in-memory bucket (window only) | **now masked in logs** |
| Stream metadata | public platform data | SQLite | public information, not PII |
| Reports | user-supplied text | SQLite | counted in stats |

**Implemented (Sprint 11.2):** IP addresses were previously written to logs
in full on rate-limit rejection. That is unnecessary retention of a personal
identifier for a project whose logs are indefinitely retained. Added
`mask_ip()` — logs keep the /24 (IPv4) or /64 (IPv6) prefix plus a short
digest for correlation, dropping the host part. The in-memory bucket key is
unchanged, so rate limiting still works exactly as before. Tests assert raw
IPs never appear in logs while prefix and correlation survive.

## 5. Platform-specific abuse

**Evaluated:** using search to target a streamer for harassment; using one
platform's metadata to harass there.

**Findings:** this is intent, not signal. Without content classification
the system cannot distinguish `wildfire` from a targeted query. The product
does not surface personal contact information, and results link to the
platform — where that platform's own moderation applies.

**Decision:** no control. Deliberately out of scope; the existing report
mechanism (Sprint 2.3) is the user-facing path.

---

## Summary

| Area | Decision |
|---|---|
| Spam queries | Already controlled (10.2); no additions |
| Malicious metadata | Already safe by construction; tests added |
| Doxxing-style searches | No control — accepted risk, documented |
| PII exposure | **One change: IP masking in logs** |
| Platform-specific abuse | No control — out of scope, documented |

**What was deliberately not built:** keyword blocklists, a content
classifier, `is_mature` filtering (still an open product decision from
Sprint 9.2), and query logging for "abuse forensics" — the last of which
would itself be the privacy violation.
