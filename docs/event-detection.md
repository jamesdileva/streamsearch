# Advanced Event Detection — Experiment (Sprint 13.2)

> Can multiple broadcasts be grouped around one ongoing event?
> Researched and measured 2026-10-10 with live YouTube data (real key) and
> a labeled fixture set.

**Verdict: works on real data for the case that matters, at a small scale.
Keep as an inspectable prototype (`GET /api/events?q=`); do not wire into
search yet.** Not a NO-GO like 13.1 — this one earned a different answer.

---

## What was wrong before

Sprint 6.3 tried clustering on token overlap and failed in a specific,
reproducible way: an LA fire stream and an LA traffic stream merged because
they share the city word. Shared *context* was treated as shared *event*.

## What 13.2 changes

Three rules, in `app/search/events.py`:

1. **Shared event family required.** Streams must share a curated event
   family (`fire`, `weather`, `concert`, …). A shared city or filler word is
   not an event.
2. **Identical family sets required.** A stream carrying a second,
   different family ("fire and storm") cannot bridge two unrelated events.
3. **Shared named entity required.** Beyond the family term, the two must
   share a non-generic word (a proper noun or place token). This rule was
   added *because* of real-data measurement, not in advance.
4. Location disagreement vetoes; location OR time must agree.

## Measurement

**Labeled fixture set (recall + precision), 8 tests in
`tests/test_event_detection.py`:**
- recall 2/2 — both known same-event groups detected (3-broadcast wildfire,
  2-broadcast concert);
- precision 5/5 — every unrelated group kept apart, including the exact
  6.3 regression (LA fire vs LA traffic), conflicting-terms
  ("fire and storm" vs "storm"), same-event-different-city, and
  same-city-different-event.

**Live YouTube data (real key, 2026-10-10):**

| Query | Streams | Proposals | Correct? |
|---|---|---|---|
| `storm` | 10 | 1 (all 10 — Hurricane Isaias) | ✅ one event, many broadcasts |
| `wildfire` | 6 | 0 | ✅ no false merge |

**A real false positive that measurement caught:** the first attempt merged
a religious livestream ("Prophetic Wildfire Live — LIVE PROPHECY") with the
LA County Fire scanner. They share the `fire` family and nothing but
filler ("live"). That produced rule 3; after it, the false merge disappears
while the genuine 10-broadcast hurricane cluster survives.

## Honest limits

- **Sample size.** Two live queries, 16 streams. Enough to show the failure
  mode and the fix, nowhere near enough to claim production quality.
- **Confidence field is weak.** Today it is `medium` only for cross-platform
  or named-place groups, which is why the true hurricane cluster (single
  platform, no location) scores `low`. The discriminator that actually
  worked — a shared named entity — is enforced as a *rule* rather than
  reported as a *signal*, which is the main thing a real system would want.
- **The event vocabulary is curated** (7 families). The roadmap's
  "entities, related streams" want general entity extraction; this is a
  deliberately small stand-in with the Sprint 3.2 guardrail attached.
- **No dedup awareness.** A duplicated broadcast and a genuine second
  broadcast of the same event are treated identically here; 6.2 dedup runs
  before this in the pipeline, which is correct but untested together.

## Verdict

**Keep the prototype, don't ship it as a ranking feature.** What earns that
split: it solves the thing the roadmap asked (one event → many broadcasts)
and it demonstrably beats 6.3 on the failure mode. What holds it back: 16
streams of evidence, no confidence signal worth acting on, and no UI
surface that would make it useful to a searcher.

Cheapest next steps if this goes further: (a) measure on 50+ real queries
across the 3 platforms; (b) make the shared-entity overlap a reported score
instead of a boolean gate; (c) only then consider grouping in the UI.

## Sprint 13.3 (Computer Vision) — recorded here for completeness

**NO-GO, decided without an experiment.** Two independent reasons, the
first decisive:

1. **It violates an enforced product boundary.** CV means decoding video
   frames, i.e. processing media we explicitly do not download or host
   (`docs/content-boundaries.md`, enforced and tested since Sprint 11.1).
   Adopting it would mean changing the product's core legal posture, not
   adding a feature.
2. **Cost/GPU.** As assessed with the project owner: a small VLM is
   unreliable exactly for the needed discrimination (smoke vs fog, "Live
   from Highway 18"), and a large one is unaffordable via API with no local
   GPU throughput.

No experiment was run, and the doc says so plainly rather than implying a
measured result that doesn't exist.
