# Caption/Transcript Relevance — Evaluation (Sprint 13.1)

> Could transcript indexing make vague live streams discoverable?
> Researched 2026-10-10 against YouTube's official API documentation.

**Verdict: NO-GO.** Not because transcripts aren't useful, but because
legitimate access to *other people's* transcripts does not exist. Documented
as a deferred experiment; nothing was built.

---

## The idea

A live stream titled just "LIVE" is unrankable by any text ranker — there is
nothing to match. If the transcript said "welcome to the Tokyo Dome concert
tonight", a transcript-aware ranker could rescue it. That was the motivating
case (the `vague-title` gap from Sprint 7.1).

## The blocking finding

Transcript retrieval goes through the YouTube Data API:

| Method | Cost | Authorization | Who can use it |
|---|---|---|---|
| `captions.list` (track IDs) | 50 units | OAuth 2.0 | video owner |
| `captions.download` (text) | 200 units | OAuth 2.0 | **"the user to have permission to edit the video"** |

The decisive line, from the documented `captions.download` reference:

> "This method requires the user to have permission to edit the video."

Two consequences for StreamSearch:

1. **Not third-party.** We discover streams broadcast by other channels. An
   API key cannot download them; OAuth as the *owner* could, but we never
   are the owner. So every transcript we'd want to index — the ones that
   would rescue a vague title — is inaccessible.
2. **Not cheap anyway.** 50 units to list + 200 units per download per
   stream. Even for one's own channel, indexing transcripts for a
   search corpus of the size discovery produces would burn the daily quota
   almost immediately.

There is no alternative documented path: `videos.list?part=contentDetails`
only exposes a boolean `contentDetails.caption` flag (captions exist: yes/no),
never the text. Auto-generated captions are not exempted from the owner rule.

The only remaining access is undocumented/internal caption endpoints
(e.g. the player's timedtext service). Using those would be the same
reverse-engineered access we ruled out for TikTok in Sprint 12.1, so it is
not an option under this product's boundary.

## What this means for the `vague-title` gap

The gap stays open, and stays honestly labelled. It is the one failure class
in the 7.1 dataset that cannot be closed legitimately:

- keyword search: no text to match;
- semantic search (7.2b): an empty title carries no semantic signal either;
- transcripts: no legitimate access to the one text source that could help.

Practical implication: for such streams the best we can do is rank on the
other fields (views, category, freshness) and make the card show the creator
rather than pretending we know what the stream is. No change proposed here.

## Verdict and re-evaluation criteria

**NO-GO for Sprint 13.1.** Revisit only if all become true:
1. A documented API allows fetching transcripts for videos you do not own;
2. Cost is compatible with indexing a live corpus (orders of magnitude
   below 250 units/stream), or transcripts come bundled in an existing
   response;
3. Terms permit indexing that text for discovery.

Until then this experiment stays documented as evaluated-and-rejected, and
the remaining keyword work belongs to the cheap lexical fixes already
identified (small synonym map, per `docs/` decisions from Sprint 7.3).
